const fs = require('fs');

function fix(filePath, searchRegex, replaceWith) {
    let txt = fs.readFileSync(filePath, 'utf8');
    txt = txt.replace(searchRegex, replaceWith);
    fs.writeFileSync(filePath, txt);
}

// chat
fix('app/chat/page.tsx',
    /<FloatChatLogo size=\{16\} \/>\r?\n\s*<\/div>\r?\n\r?\n\s*\{\/\* ── Messages ── \*\/\}/,
    '<FloatChatLogo size={16} />\n                </div>\n            </div>\n\n            {/* ── Messages ── */}'
);
fix('app/chat/page.tsx',
    /<\/p>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*<style>/,
    '</p>\n                </div>\n            </div>\n            </div>\n\n            <style>'
);

// explorer
fix('app/explorer/page.tsx',
    /<\/button>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*\{\/\* Body \*\/\}/,
    '</button>\n                </div>\n            </div>\n            </div>\n\n            {/* Body */}'
);
fix('app/explorer/page.tsx',
    /<\/div>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*<\/div>\r?\n\s*\)/,
    '</div>\n                </div>\n            </div>\n            </div>\n\n        </div>\n    )'
);

// study
fix('app/study/page.tsx',
    /<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*\{\/\* Main Layout \*\/\}/,
    '</div>\n            </div>\n            </div>\n\n            {/* Main Layout */}'
);
fix('app/study/page.tsx',
    /<\/div>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\s*<\/div>\r?\n\r?\n\s*<\/div>\r?\n\s*\)/,
    '</div>\n                    </div>\n                </div>\n            </div>\n            </div>\n\n        </div>\n    )'
);

console.log('Fixed unmatched divs with newline tolerance!');
