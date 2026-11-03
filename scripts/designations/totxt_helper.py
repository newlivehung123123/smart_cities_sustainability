import sys,re,html
for f in sys.argv[1:]:
    t=open(f,encoding='utf-8',errors='replace').read()
    m=re.search(r'<article.*?</article>',t,re.S) or re.search(r'class="(?:entry-content|post-content|txt-article|detail-text|read__content|content-detail)[^"]*".*',t,re.S)
    b=m.group(0) if m else t
    b=re.sub(r'<(script|style|noscript).*?</\1>','',b,flags=re.S)
    b=re.sub(r'<br\s*/?>|</p>|</tr>|</li>|</h\d>|</div>','\n',b); b=re.sub(r'</t[dh]>',' | ',b)
    b=html.unescape(re.sub(r'<[^>]+>','',b))
    b='\n'.join(x.strip() for x in b.splitlines() if x.strip())
    open(f.rsplit('.',1)[0]+'.txt','w').write(b)
