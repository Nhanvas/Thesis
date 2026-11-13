import sys
from PIL import Image
ks=sys.argv[2].split(','); out=sys.argv[1]
c=Image.new('RGB',(1920*2,1080*2),'white')
for i,k in enumerate(ks[:4]):
    c.paste(Image.open(f'../preview/{k}.png'),((i%2)*1920,(i//2)*1080))
c.resize((1920,1080)).save(f'../preview/{out}.png')
