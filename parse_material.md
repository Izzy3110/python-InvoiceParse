## thought: How to extract from multiple <span> tags and group the data together using BS4?
---
## because: some parts from source invoice are the same 
  ty [alternate.de](https://www.alternate.de/) where I bought my workstation :)
  
### Original Invoice
```
<span class="ocrx_line" title="bbox 42 107 224 115">
  <span class="ocrx_word" title="bbox 42 107 80 115">ALTERNATE</span>
  <span class="ocrx_word" title="bbox 82 107 101 115">GmbH</span>
  <span class="ocrx_word" title="bbox 103 107 105 115">·</span>
  <span class="ocrx_word" title="bbox 109 107 165 115">Philipp-Reis-Straße</span>
  <span class="ocrx_word" title="bbox 167 107 177 115">2-3</span>
  <span class="ocrx_word" title="bbox 178 107 180 115">·</span>
  <span class="ocrx_word" title="bbox 184 107 202 115">35440</span>
  <span class="ocrx_word" title="bbox 204 107 224 115">Linden</span>
</span>
```
---
### Stackoverflow Example-Content:
```
<p class="Paragraph SCX">
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            This week
        </span>
    </span>
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            &nbsp;(12/
        </span>
    </span>
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            11
        </span>
    </span>
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            &nbsp;- 12/1
        </span>
    </span>
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            7
        </span>
    </span>
    <span class="TextRun SCX">
        <span class="NormalTextRun SCX">
            ):
        </span>
    </span>
    <span class="EOP SCX">
        &nbsp;
    </span>
</p>
```

## parse-with:
```from bs4 import BeautifulSoup
soup = BeautifulSoup(content,'lxml')
data = ''.join([' '.join(item.text.split()) for item in soup.select(".NormalTextRun")])
print(data)
```

### Output:

This week(12/11- 12/17):


source: [Stackoverflow](https://stackoverflow.com/questions/47863031/how-to-extract-from-multiple-span-tags-and-group-the-data-together-using-bs4)

