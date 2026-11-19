import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD="/usr/share/fonts/truetype/google-fonts/"
B=lambda s: ImageFont.truetype(FD+"Poppins-Bold.ttf",s); M=lambda s: ImageFont.truetype(FD+"Poppins-Medium.ttf",s)
NAVY=(14,18,34); PINK=(255,62,140); ORANGE=(255,150,60); WHITE=(255,255,255); SOFT=(190,198,215)
OUT="/home/claude/guide-gta6/fanpage/media/edits"; os.makedirs(OUT,exist_ok=True)
HANDLE="@gta6belgique"

def sunset_bg(w,h):
    im=Image.new("RGB",(w,h),NAVY); d=ImageDraw.Draw(im)
    for y in range(h):  # dégradé nuit vers violet
        t=y/h; d.line([(0,y),(w,y)],fill=(int(14+40*t),int(18+8*t),int(34+40*t)))
    return im

def avatar():
    S=1080; im=sunset_bg(S,S); d=ImageDraw.Draw(im)
    for i,c in enumerate([(255,62,140),(255,100,110),(255,150,60)]):
        d.ellipse([290+i*0,250+i*0,790,750],fill=c) if i==0 else None
    # soleil couchant à bandes
    sun=Image.new("RGB",(S,S),(0,0,0)); m=Image.new("L",(S,S),0); sd=ImageDraw.Draw(sun); md=ImageDraw.Draw(m)
    for y in range(240,760):
        t=(y-240)/520; sd.line([(0,y),(S,y)],fill=(255,int(62+90*t),int(140-80*t)))
    md.ellipse([290,240,790,740],fill=255)
    for k,y in enumerate(range(560,740,34)): md.rectangle([0,y,S,y+8+k*3],fill=0)
    im.paste(sun,(0,0),m); d=ImageDraw.Draw(im)
    f=B(250); t="G6"; w=d.textlength(t,font=f); d.text(((S-w)/2,610),t,font=f,fill=WHITE,stroke_width=10,stroke_fill=NAVY)
    im.save(OUT+"/avatar-1080.png")

def banner():
    W,H=2560,1440; im=sunset_bg(W,H); d=ImageDraw.Draw(im)
    d.ellipse([W/2-380,300,W/2+380,1060],fill=(255,62,140)); d.rectangle([0,690,W,H],fill=(20,22,44))
    for y in range(700,760,14): d.line([(0,y),(W,y)],fill=(255,120,90),width=3)
    # zone sûre centrale 1546x423
    f=B(120); t="GTA 6 BELGIQUE"; w=d.textlength(t,font=f); d.text(((W-w)/2,560),t,font=f,fill=WHITE,stroke_width=6,stroke_fill=NAVY)
    f2=M(52); t2="Astuces · secrets cachés · actus vérifiées"; w2=d.textlength(t2,font=f2); d.text(((W-w2)/2,720),t2,font=f2,fill=WHITE)
    f3=M(34); t3="Fan page non affiliée à Rockstar Games"; w3=d.textlength(t3,font=f3); d.text(((W-w3)/2,800),t3,font=f3,fill=SOFT)
    im.save(OUT+"/banniere-youtube-2560x1440.png")

def wrap(d,text,font,maxw):
    out=[];cur=""
    for word in text.split():
        t=(cur+" "+word).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: out.append(cur); cur=word
    out.append(cur); return out

def slide(path, kicker, text, idx, n, hook=False):
    W,H=1080,1920; im=sunset_bg(W,H); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,14],fill=PINK)
    if kicker: d.text((90,330),kicker,font=B(46),fill=PINK)
    size=112 if hook else 84
    while True:
        f=B(size); lines=wrap(d,text,f,W-180)
        if len(lines)*size*1.18<=760 or size<56: break
        size-=6
    y=(H-len(lines)*size*1.18)/2
    for l in lines: d.text((90,y),l,font=f,fill=WHITE,stroke_width=4 if hook else 0,stroke_fill=NAVY); y+=size*1.18
    # barre de progression et pied (hors zone UI basse des Shorts)
    d.rectangle([90,1500,90+(W-180)*(idx+1)/n,1510],fill=ORANGE); d.rectangle([90+(W-180)*(idx+1)/n,1500,W-90,1510],fill=(60,60,90))
    d.text((90,1530),HANDLE,font=M(40),fill=SOFT)
    d.text((90,1580),"Fan page · non affiliée à Rockstar Games",font=M(30),fill=(140,148,170))
    im.save(path)

def short(name, slides, durs):
    os.makedirs("frames/"+name,exist_ok=True); files=[]
    for i,(k,t) in enumerate(slides):
        p=f"frames/{name}/{i:02d}.png"; slide(p,k,t,i,len(slides),hook=(i==0)); files.append(p)
    args=["ffmpeg","-y","-loglevel","error"]
    for p,dur in zip(files,durs): args+=["-loop","1","-t",str(dur+0.4),"-i",p]
    fc=""; prev="[0:v]"; off=0
    for i in range(1,len(files)):
        off+=durs[i-1]; lab=f"[v{i}]"; fc+=f"{prev}[{i}:v]xfade=transition=fade:duration=0.4:offset={off:.2f}{lab};"; prev=lab
    fc+=f"{prev}format=yuv420p,fps=30[out]"
    args+=["-filter_complex",fc,"-map","[out]","-c:v","libx264","-preset","medium","-crf","20","-movflags","+faststart",f"{OUT}/{name}.mp4"]
    subprocess.run(args,check=True)
    return sum(durs)

avatar(); banner()
S=[
("short-01-gta6-est-sorti",[
 ("", "GTA 6 EST SORTI : 3 TRUCS À FAIRE AVANT DE JOUER"),
 ("1. LA PLACE", "Sur PS5, le jeu demande jusqu'à 212 Go. Fais de la place avant."),
 ("2. LA BOÎTE", "Dans la boîte en magasin : un code de téléchargement, pas de disque."),
 ("3. LE BONUS", "Pack Vice City Vintage offert pour tout achat avant le 20 novembre."),
 ("", "Abonne-toi pour d'autres astuces GTA 6")],[2.6,3.4,3.4,3.6,2.6]),
("short-02-ps5-pleine",[
 ("", "TA PS5 EST PLEINE POUR GTA 6 ?"),
 ("ÉTAPE 1", "Paramètres, puis Stockage, puis Stockage de la console."),
 ("ÉTAPE 2", "Supprime les jeux terminés : tes sauvegardes restent sur la console."),
 ("ÉTAPE 3", "Vise 212 Go libres. Toujours pas assez ? Un SSD compatible PS5 avec dissipateur."),
 ("", "Enregistre ce Short pour plus tard")],[2.4,3.2,3.4,3.8,2.4]),
("short-03-gta6-pc",[
 ("", "GTA 6 SUR PC ? LA VRAIE RÉPONSE"),
 ("AUJOURD'HUI", "GTA 6 sort seulement sur PS5 et Xbox Series X|S."),
 ("ET LE PC ?", "Rockstar n'a annoncé aucune date pour la version PC."),
 ("DONC", "Méfie-toi des sites qui vendent « GTA 6 PC » : c'est une arnaque."),
 ("", "On te prévient dès que Rockstar annonce quelque chose")],[2.4,3.0,3.0,3.4,2.6]),
]
for n,s,du in S: print(n, round(short(n,s,du),1),"s")
