import subprocess,re,sys
pdf=sys.argv[1]
n=int(re.search(r'Pages:\s+(\d+)',subprocess.run(['pdfinfo',pdf],capture_output=True,text=True).stdout).group(1))
marks={}
for i in range(1,n+1):
    t=subprocess.run(['pdftotext','-f',str(i),'-l',str(i),'-layout',pdf,'-'],capture_output=True,text=True).stdout
    lines=[l.strip() for l in t.splitlines() if l.strip()]
    for l in lines[:8]:
        for key in ['CHAPTER 1:','CHAPTER 2:','CHAPTER 3:','CHAPTER 4:','CHAPTER 5:','REFERENCES','APPENDICES','ABSTRACT','TABLE OF CONTENTS']:
            if l.startswith(key) and key not in marks: marks[key]=(i,lines[-1])
print(n, marks)
c1=marks['CHAPTER 1:'][0]; r=marks['REFERENCES'][0]; a=marks['APPENDICES'][0]
print('body pages (Ch1..Ch5):', r-c1, '| chapters:', {k:marks[k][0] for k in marks}, '| references', a-r, '| appendix', n-a+1)
