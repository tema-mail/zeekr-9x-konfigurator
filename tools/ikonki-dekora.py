"""Иконки декора кузова: вырезка решётки из официального рендера (спереди ¾). У Zeekr в двух иконках китайский текст."""
from PIL import Image
SRC = {'Z011PC021': 'Z011PC012_Z011PC002_Z011PC021_Z011PC026', 'Z011PC020': 'Z011PC012_Z011PC004_Z011PC020_Z011PC026',
       'Z011PC022': 'Z011PC012_Z011PC003_Z011PC022_Z011PC026', 'Z011PC023': 'Z011PC012_Z011PC002_Z011PC023_Z011PC026',
       'Z011PC038': 'Z011PC012_Z011PC002_Z011PC038_Z011PC039'}
for pc, code in SRC.items():
    im = Image.open(f'img/zeekr-9x/ext/{code}--front34.webp').convert('RGB')
    box = (25, 280, 255, 510)
    im.crop(box).resize((112, 112), Image.LANCZOS).save(f'img/zeekr-9x/options/{pc}.webp', 'WEBP', quality=85)
print('ok')
