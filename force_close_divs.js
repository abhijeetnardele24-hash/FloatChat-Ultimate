const fs = require('fs');

const file = 'app/chat/page.tsx';
let txt = fs.readFileSync(file, 'utf8');

txt = txt.replace('                <FloatChatLogo size={16} />\n            </div>\n\n            {/* ── Messages ── */}', '                <FloatChatLogo size={16} />\n                </div>\n            </div>\n\n            {/* ── Messages ── */}');

txt = txt.replace('                    </p>\n                </div>\n            </div>\n\n            <style>{`', '                    </p>\n                </div>\n            </div>\n            </div>\n\n            <style>{`');

fs.writeFileSync(file, txt);

// explorer
const exp = 'app/explorer/page.tsx';
let e = fs.readFileSync(exp, 'utf8');
e = e.replace('                    </button>\n                </div>\n            </div>\n\n            {/* Body */}', '                    </button>\n                </div>\n            </div>\n            </div>\n\n            {/* Body */}');
e = e.replace('                    </div>\n                </div>\n            </div>\n\n        </div>\n    )', '                    </div>\n                </div>\n            </div>\n            </div>\n\n        </div>\n    )');
fs.writeFileSync(exp, e);

// study
const std = 'app/study/page.tsx';
let s = fs.readFileSync(std, 'utf8');
s = s.replace('                </div>\n            </div>\n\n            {/* Main Layout */}', '                </div>\n            </div>\n            </div>\n\n            {/* Main Layout */}');
s = s.replace('                        </div>\n                    </div>\n                </div>\n            </div>\n\n        </div>\n    )', '                        </div>\n                    </div>\n                </div>\n            </div>\n            </div>\n\n        </div>\n    )');
fs.writeFileSync(std, s);
