import os
import json
import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import FileSystemStorage
from androguard.misc import AnalyzeAPK
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def get_latest_version_info(package_name):
    base_dir = os.path.join('apk', package_name)
    if not os.path.exists(base_dir):
        return None

    highest_version = None
    highest_version_path = None

    for version_code in os.listdir(base_dir):
        info_file_path = os.path.join(base_dir, version_code, 'info.json')
        if os.path.exists(info_file_path):
            with open(info_file_path, 'r') as info_file:
                apk_info = json.load(info_file)
                if highest_version is None or int(apk_info['version_code']) > int(highest_version):
                    highest_version = apk_info['version_code']
                    highest_version_path = info_file_path

    if highest_version_path:
        with open(highest_version_path, 'r') as info_file:
            return json.load(info_file)

    return None

@method_decorator(csrf_exempt, name='dispatch')
class UploadAPKView(View):
    def post(self, request):
        if 'apk' not in request.FILES:
            return JsonResponse({'error': 'No APK file uploaded'}, status=400)

        apk_file = request.FILES['apk']

        fs = FileSystemStorage()
        temp_filename = fs.save(apk_file.name, apk_file)
        temp_file_path = fs.path(temp_filename)

        try:
            a, d, dx = AnalyzeAPK(temp_file_path)
            package_name = a.get_package()
            version_code = a.get_androidversion_code()
            app_name = a.get_app_name()
            version_name = a.get_androidversion_name()
            permissions = a.get_permissions()
            app_size = apk_file.size / 1024  # Size in KB

            # Extract the app icon
            icon_path = a.get_app_icon()
            icon_base64 = None
            if icon_path:
                icon_data = a.get_file(icon_path)
                icon_base64 = base64.b64encode(icon_data).decode('utf-8')

                # Save the icon to a file
                icon_save_path = os.path.join('apk', package_name, str(version_code), 'icon.png')
                os.makedirs(os.path.dirname(icon_save_path), exist_ok=True)
                with open(icon_save_path, 'wb') as icon_file:
                    icon_file.write(icon_data)
            else:
                icon_save_path = None

            # Define the new path for saving the APK file
            save_dir = os.path.join('apk', package_name, str(version_code))
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, apk_file.name)
            with open(save_path, 'wb') as f:
                for chunk in apk_file.chunks():
                    f.write(chunk)

            # Create a dictionary for the APK info
            apk_info = {
                'package_name': package_name,
                'version_code': version_code,
                'app_name': app_name,
                'version_name': version_name,
                'permissions': permissions,
                'app_size': app_size,
                'file_path': save_path,
                'icon_base64': icon_base64,
                'icon_path': icon_save_path
            }

            # Save the APK info to a JSON file
            info_file_path = os.path.join(save_dir, 'info.json')
            with open(info_file_path, 'w') as info_file:
                json.dump(apk_info, info_file, indent=4)

            # Clean up the temporary file
            os.remove(temp_file_path)

            return JsonResponse(apk_info)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class APKInfoView(View):
    def get(self, request, package_name):
        apk_info = get_latest_version_info(package_name)
        if apk_info is None:
            return JsonResponse({'error': 'APK info not found'}, status=404)

        return JsonResponse(apk_info)



class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class WebView(View):
    def get(self, request):
        return render(request, 'frontend/web/build/index.html')