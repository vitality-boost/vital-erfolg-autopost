# vital.erfolg – Render-Engine (Markenfarben, 4 Einzel-Layouts + Karussell-Slides)
# Wird sowohl lokal als auch im Composio-Sandbox (Auto-Poster) genutzt.
import glob, os
from PIL import Image, ImageDraw, ImageFont

NAVY=(7,23,57); BODY=(75,99,130); LIGHT=(164,181,196); BOX=(205,213,219)
BRONZE=(166,136,104); CREAM=(227,195,157); WHITE=(245,247,250)
W,H=1080,1350

def _find(name):
    for pat in ("/usr/share/fonts/**/"+name,):
        m=glob.glob(pat,recursive=True)
        if m: return m[0]
    raise FileNotFoundError(name)
FB=_find("LiberationSans-Bold.ttf")
try: FR=_find("LiberationSans-Regular.ttf")
except Exception: FR=FB
def fo(s,b=True): return ImageFont.truetype(FB if b else FR,s)
def twd(d,t,f): return d.textlength(t,font=f)
def fit(d,lines,maxw,hi,lo):
    for s in range(hi,lo-1,-2):
        f=fo(s)
        if all(d.textlength(t,font=f)<=maxw for t in lines): return s
    return lo

def _bars(d): d.rectangle([0,0,W,12],fill=BRONZE); d.rectangle([0,H-12,W,H],fill=BRONZE)
def _handle(d,txt="vital.erfolg"): d.text((80,70),txt,font=fo(34),fill=LIGHT)
def _pill(d,cta):
    ps=fit(d,[cta],760,40,26); pf=fo(ps)
    pb=d.textbbox((0,0),cta,font=pf); ptw=pb[2]-pb[0]
    pad_x,pad_y=46,32; aw=int(ps*1.6); pw=ptw+2*pad_x+aw; ph=(pb[3]-pb[1])+2*pad_y
    px,py=80,H-ph-130
    d.rounded_rectangle([px,py,px+pw,py+ph],radius=ph//2,fill=BRONZE)
    cx=px+pad_x+18; cy=py+ph//2
    d.line([(cx-16,cy-12),(cx,cy+12),(cx+16,cy-12)],fill=NAVY,width=9,joint="curve")
    d.text((px+pad_x+aw,py+pad_y-4),cta,font=pf,fill=NAVY)
def _swipe(d,idx,total):
    # page dots + arrow for carousels
    d.text((80,H-150),f"{idx}/{total}",font=fo(34),fill=LIGHT)
    cta="weiterwischen"
    pf=fo(36); ptw=twd(d,cta,pf)
    d.text((W-80-ptw,H-152),cta,font=pf,fill=CREAM)

def _new():
    img=Image.new("RGB",(W,H),NAVY); return img,ImageDraw.Draw(img)

# ---- Einzel-Layouts ----
def render_A(p):
    img,d=_new(); _bars(d); _handle(d)
    L=[p["line1"],p["line2"],p["line3"]]
    fs=fit(d,L,920,118,72); f=fo(fs); lh=int(fs*1.18)
    total=lh*3+40+70; y=int((H-total)/2)-40
    for t,c in zip(L,[WHITE,BRONZE,WHITE]): d.text((80,y),t,font=f,fill=c); y+=lh
    y+=20; ss=fit(d,[p["subline"]],920,58,34)
    d.text((84,y),p["subline"],font=fo(ss),fill=LIGHT)
    _pill(d,p["pill"]); return img
def render_B(p):
    img,d=_new(); _bars(d); _handle(d)
    big=fo(300); s=p["stat"]
    d.text(((W-twd(d,s,big))/2,300),s,font=big,fill=BRONZE)
    sub=fo(64)
    for i,l in enumerate(p["lines"]): d.text(((W-twd(d,l,sub))/2,640+i*84),l,font=sub,fill=WHITE)
    sm=fo(44,False); t=p["subline"]
    d.text(((W-twd(d,t,sm))/2,860),t,font=sm,fill=LIGHT)
    _pill(d,p["pill"]); return img
def render_C(p):
    img,d=_new(); _bars(d); _handle(d)
    d.text((80,290),"MYTHOS",font=fo(40),fill=LIGHT)
    mf=fo(58)
    for i,l in enumerate(p["mythos"]): d.text((80,350+i*72),l,font=mf,fill=BODY)
    py=600; ph=470; d.rounded_rectangle([60,py,W-60,py+ph],radius=28,fill=BRONZE)
    d.text((100,py+36),"FAKT",font=fo(40),fill=NAVY)
    ff=fo(54)
    for i,l in enumerate(p["fakt"]): d.text((100,py+104+i*74),l,font=ff,fill=NAVY)
    _pill(d,p["pill"]); return img
def render_D(p):
    img,d=_new(); _bars(d); _handle(d)
    d.text((78,250),"“",font=fo(260),fill=BRONZE)
    qf=fo(82); y=520
    for l,c in p["quote"]: d.text((80,y),l,font=qf,fill=(CREAM if c=="cream" else WHITE)); y+=104
    d.text((84,y+24),p.get("attribution","— vital.erfolg"),font=fo(40),fill=LIGHT)
    _pill(d,p["pill"]); return img

# ---- Karussell-Slides ----
def slide_hook(s,idx,total):
    img,d=_new(); _bars(d); _handle(d)
    L=[s["line1"],s["line2"],s["line3"]]
    fs=fit(d,L,920,110,68); f=fo(fs); lh=int(fs*1.18)
    tot=lh*3+40+60; y=int((H-tot)/2)-60
    for t,c in zip(L,[WHITE,BRONZE,WHITE]): d.text((80,y),t,font=f,fill=c); y+=lh
    y+=20; ss=fit(d,[s["subline"]],920,52,32)
    d.text((84,y),s["subline"],font=fo(ss),fill=LIGHT)
    _swipe(d,idx,total); return img
def slide_point(s,idx,total):
    img,d=_new(); _bars(d); _handle(d)
    d.text((80,260),s["tag"],font=fo(150),fill=BRONZE)  # big number/emoji
    hf=fit(d,[s["heading"]],920,72,44)
    d.text((80,470),s["heading"],font=fo(hf),fill=WHITE)
    bf=fo(50,False); y=600
    for l in s["body"]: d.text((80,y),l,font=bf,fill=LIGHT); y+=66
    _swipe(d,idx,total); return img
def slide_cta(s,idx,total):
    img,d=_new(); _bars(d); _handle(d)
    hf=fo(76); y=380
    for l in s["lines"]: d.text((80,y),l,font=hf,fill=WHITE); y+=96
    d.text((80,y+30),s.get("sub",""),font=fo(48,False),fill=CREAM)
    _pill(d,s.get("pill","Folge für mehr → vital.erfolg")); return img

def render_item(item, outdir, prefix):
    """Rendert ein Queue-Item. Gibt geordnete Liste der PNG-Pfade zurueck."""
    os.makedirs(outdir,exist_ok=True)
    paths=[]
    if item.get("format")=="carousel":
        slides=item["slides"]; total=len(slides)
        for i,s in enumerate(slides,1):
            t=s["type"]
            if t=="hook": img=slide_hook(s,i,total)
            elif t=="point": img=slide_point(s,i,total)
            else: img=slide_cta(s,i,total)
            fp=os.path.join(outdir,f"{prefix}_{item['id']}_s{i}.png"); img.save(fp,quality=95); paths.append(fp)
    else:
        tpl=item["template"]; f={"A":render_A,"B":render_B,"C":render_C,"D":render_D}[tpl]
        img=f(item["fields"]); fp=os.path.join(outdir,f"{prefix}_{item['id']}.png"); img.save(fp,quality=95); paths.append(fp)
    return paths
