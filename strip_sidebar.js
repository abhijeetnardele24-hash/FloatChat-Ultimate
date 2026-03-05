const fs = require('fs')

let content = fs.readFileSync('app/chat/page.tsx', 'utf8')

// Remove Sidebar from chat page
let r1 = /\{\/\*\s*──\s*Left Sidebar Navigation\s*──\s*\*\/\}(?:[\s\S]*?(?=\{\/\*\s*──\s*Chat Main Area\s*──\s*\*\/\s*<div style=\{\{\s*flex:\s*1,\s*display:\s*'flex',\s*flexDirection:\s*'column',\s*position:\s*'relative',\s*zIndex:\s*10\s*\}\}\>))/;
if (r1.test(content)) {
    content = content.replace(r1, '');
}

// Remove Chat Main Area wrapper div because we are now the whole page
let r2 = /\{\/\*\s*──\s*Chat Main Area\s*──\s*\*\/\s*<div style=\{\{\s*flex:\s*1,\s*display:\s*'flex',\s*flexDirection:\s*'column',\s*position:\s*'relative',\s*zIndex:\s*10\s*\}\}\>/;
if (r2.test(content)) {
    content = content.replace(r2, '');

    // We also need to remove the matching closing div for Chat Main Area at the very bottom
    // The outermost wrapper was <div style={{ backgroundColor...
    // Let's just find the last </div> before <style> and pop it.
    let lines = content.split('\n')
    let styleIdx = -1
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].includes('<style>')) {
            styleIdx = i
            break
        }
    }

    if (styleIdx > 0) {
        // find the preceding </div>
        for (let i = styleIdx - 1; i >= 0; i--) {
            if (lines[i].includes('</div>')) {
                lines.splice(i, 1) // Remove one closing div
                break
            }
        }
    }
    content = lines.join('\n')
}

// Ensure the page takes full height correctly by removing flexDirection: 'row'
let r3 = /<div style=\{\{\s*backgroundColor:\s*'#f5f5f7',\s*height:\s*'100vh',\s*display:\s*'flex',\s*flexDirection:\s*'row'/;
if (r3.test(content)) {
    content = content.replace(r3, "<div style={{ backgroundColor: '#f5f5f7', height: '100vh', display: 'flex', flexDirection: 'column'");
}


fs.writeFileSync('app/chat/page.tsx', content)
console.log('Stripped local sidebar from chat page')
