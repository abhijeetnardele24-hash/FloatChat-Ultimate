const fs = require('fs');
let file = 'app/chat/page.tsx';
let content = fs.readFileSync(file, 'utf8');

// The string we are looking for is exactly at the end.
content = content.replace(
    /<\/div>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*<style>/,
    '</div>\n            </div>\n\n            <style>'
);

fs.writeFileSync(file, content);
console.log('Fixed extra div!');
