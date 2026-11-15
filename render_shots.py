import subprocess
import os

pages = ['index.html', 'types.html', 'safety.html', 'profile.html', 'gallery.html', 'contact.html', '3d-view.html']

for page in pages:
    name = page.replace('.html', '')
    p = os.path.abspath(page).replace('\\', '/')
    url = f'file:///{p}'
    
    # Desktop standard viewport
    subprocess.run([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        r'--user-data-dir=C:\Users\hplap\AppData\Local\Temp\cd_test',
        f'--screenshot=C:\\Users\\hplap\\OneDrive\\Desktop\\files\\verify_{name}_desktop.png',
        '--window-size=1600,1050',
        url
    ])
    
    # Desktop full page viewport
    subprocess.run([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        r'--user-data-dir=C:\Users\hplap\AppData\Local\Temp\cd_test',
        f'--screenshot=C:\\Users\\hplap\\OneDrive\\Desktop\\files\\verify_{name}_full.png',
        '--window-size=1600,2000',
        url
    ])
    
    # Mobile viewport (matching concept phone mockup)
    subprocess.run([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new',
        r'--user-data-dir=C:\Users\hplap\AppData\Local\Temp\cd_test',
        '--hide-scrollbars',
        f'--screenshot=C:\\Users\\hplap\\OneDrive\\Desktop\\files\\verify_{name}_mobile.png',
        '--window-size=504,860',
        url
    ])

print('All verification screenshots generated!')

