const fs = require('fs');
const path = require('path');

// Fix Chat Page
let chatPath = path.join(__dirname, 'app/chat/page.tsx');
let chatCss = fs.readFileSync(chatPath, 'utf8');

chatCss = chatCss.replace(
    /\{\/\* ── Header ── \*\/\}[\s\S]*?<div style=\{\{[^\}]*borderTop:\s*'none'[^\}]*\}\}>/,
    `{/* ── Header ── */}
            <div style={{ padding: '16px 20px 0', display: 'flex', justifyContent: 'center', flexShrink: 0, zIndex: 50, position: 'relative' }}>
                <div style={{ ...GLASS, borderRadius: 99, width: '100%', maxWidth: 1100, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 24px', gap: 12 }}>`
).replace(
    /\{\/\* Input Area \*\/\}[\s\S]*?<div style=\{\{[^\}]*borderBottom:\s*'none'[^\}]*\}\}>/,
    `{/* Input Area */}
            <div style={{ padding: '0 20px 20px', display: 'flex', justifyContent: 'center', flexShrink: 0, zIndex: 30, position: 'relative' }}>
                <div style={{ ...GLASS, borderRadius: 32, width: '100%', maxWidth: 860, padding: '16px 20px', boxShadow: '0 12px 40px rgba(0,0,0,0.15)' }}>`
);
fs.writeFileSync(chatPath, chatCss);

// Fix Explorer Page
let expPath = path.join(__dirname, 'app/explorer/page.tsx');
let expCss = fs.readFileSync(expPath, 'utf8');

expCss = expCss.replace(
    /\{\/\* Header \*\/\}[\s]*<div style=\{\{\s*\.\.\.GLASS\s*,[^>]+borderTop:\s*'none',[^>]+justifyContent:\s*'space-between',\s*flexShrink:\s*0\s*\}\}>/,
    `{/* Header */}
            <div style={{ padding: '16px 20px 0', display: 'flex', justifyContent: 'center', flexShrink: 0, zIndex: 50, position: 'relative' }}>
                <div style={{ ...GLASS, borderRadius: 99, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 24px', gap: 12 }}>`
).replace(
    /\{\/\* Body \*\/\}[\s]*<div style=\{\{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative', zIndex: 10 \}\}>[\s]*\{\/\* Filter sidebar \*\/\}[\s]*<AnimatePresence initial=\{false\}>[\s]*\{showFilters && \([\s]*<motion\.div initial=\{\{ width: 0, opacity: 0 \}\} animate=\{\{ width: 340, opacity: 1 \}\} exit=\{\{ width: 0, opacity: 0 \}\} transition=\{\{ duration: 0\.3 \}\} style=\{\{ overflow: 'hidden' \}\}>/,
    `{/* Body */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative', zIndex: 10, padding: '16px 20px', gap: 16 }}>
                {/* Filter sidebar */}
                <AnimatePresence initial={false}>
                    {showFilters && (
                        <motion.div initial={{ width: 0, opacity: 0, marginRight: 0 }} animate={{ width: 340, opacity: 1, marginRight: 16 }} exit={{ width: 0, opacity: 0, marginRight: 0 }} transition={{ duration: 0.3 }} style={{ overflow: 'hidden', borderRadius: 28 }}>`
).replace(
    /\{\/\* Left Sidebar \*\/\}\s*<div style=\{\{ \.\.\.GLASS, width: 340, display: 'flex', flexDirection: 'column', borderTop: 'none', borderBottom: 'none', borderLeft: 'none', borderRadius: 0 \}\}>/,
    `{/* Left Sidebar */}
                            <div style={{ ...GLASS, width: 340, height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 28, border: '1px solid rgba(255,255,255,0.88)' }}>`
).replace(
    /\{\/\* Main UI \*\/\}\s*<div style=\{\{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' \}\}>/,
    `{/* Main UI */}
                <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', borderRadius: 28, overflow: 'hidden', ...GLASS }}>`
);
fs.writeFileSync(expPath, expCss);

// Fix Study Page
let studyPath = path.join(__dirname, 'app/study/page.tsx');
let studyCss = fs.readFileSync(studyPath, 'utf8');
studyCss = studyCss.replace(
    /\{\/\* Header \*\/\}[\s]*<div style=\{\{\s*\.\.\.GLASS\s*,[^>]+borderTop:\s*'none',[^>]+justifyContent:\s*'space-between',\s*flexShrink:\s*0\s*\}\}>/,
    `{/* Header */}
            <div style={{ padding: '16px 20px 0', display: 'flex', justifyContent: 'center', flexShrink: 0, zIndex: 50, position: 'relative' }}>
                <div style={{ ...GLASS, borderRadius: 99, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 24px', gap: 12 }}>`
).replace(
    /\{\/\* Main Layout \*\/\}[\s]*<div style=\{\{ flex: 1, display: 'flex', overflow: 'hidden', zIndex: 10 \}\}>[\s]*\{\/\* Left Sidebar \*\/\}[\s]*<div style=\{\{\s*\.\.\.GLASS\s*,[^>]+borderTop:\s*'none',[^>]+borderRadius:\s*0\s*\}\}>/,
    `{/* Main Layout */}
            <div style={{ flex: 1, display: 'flex', overflow: 'hidden', zIndex: 10, padding: '16px 20px 20px', gap: 16 }}>
                {/* Left Sidebar */}
                <div style={{ ...GLASS, width: 320, display: 'flex', flexDirection: 'column', flexShrink: 0, borderRadius: 28, position: 'relative' }}>`
).replace(
    /\{\/\* Sub-header \*\/\}\s*<div style=\{\{ padding: '12px 16px', borderBottom: '1px solid rgba\(0,0,0,0\.06\)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' \}\}>/,
    `{/* Sub-header */}
                    <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(0,0,0,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>`
).replace(
    /\{\/\* Main Content Area \*\/\}\s*<div style=\{\{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', background: 'rgba\(255,255,255,0\.4\)' \}\}>/,
    `{/* Main Content Area */}
                <div style={{ ...GLASS, flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', borderRadius: 28 }}>`
).replace(
    /\{\/\* WS Header \*\/\}\s*<div style=\{\{ padding: '16px 24px', borderBottom: '1px solid rgba\(0,0,0,0\.06\)', background: 'rgba\(255,255,255,0\.65\)', backdropFilter: 'blur\(16px\)', zIndex: 20 \}\}>/,
    `{/* WS Header */}
                    <div style={{ padding: '20px 28px', borderBottom: '1px solid rgba(0,0,0,0.08)', background: 'rgba(255,255,255,0.4)', backdropFilter: 'blur(20px)', zIndex: 20 }}>`
);
fs.writeFileSync(studyPath, studyCss);

// Fix Tools Page
let toolsPath = path.join(__dirname, 'app/tools/page.tsx');
let toolsCss = fs.readFileSync(toolsPath, 'utf8');
toolsCss = toolsCss.replace(
    /\{\/\* Floating Pill Nav \*\/\}[\s]*<div style=\{\{ position: 'fixed', top: 16, left: '50%', transform: 'translateX\(-50%\)', zIndex: 50, width: '90%', maxWidth: 860 \}\}>[\s]*<div style=\{\{ \.\.\.GLASS, borderRadius: 99, padding: '10px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 0 rgba\(255,255,255,0\.9\) inset, 0 8px 32px rgba\(0,0,0,0\.12\)' \}\}>/,
    `{/* Floating Pill Nav */}
            <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 50, width: '90%', maxWidth: 960 }}>
                <div style={{ ...GLASS, borderRadius: 99, padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 0 rgba(255,255,255,0.9) inset, 0 12px 36px rgba(0,0,0,0.1)' }}>`
);
fs.writeFileSync(toolsPath, toolsCss);

// Fix Visualizations Page
let visPath = path.join(__dirname, 'app/visualizations/page.tsx');
let visCss = fs.readFileSync(visPath, 'utf8');
visCss = visCss.replace(
    /\{\/\* ── Floating nav pill ── \*\/\}[\s]*<div style=\{\{ position: 'fixed', top: 16, left: '50%', transform: 'translateX\(-50%\)', zIndex: 50, width: '92%', maxWidth: 1000 \}\}>[\s]*<div style=\{\{ \.\.\.GLASS, borderRadius: 99, padding: '10px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 0 rgba\(255,255,255,0\.9\) inset, 0 8px 32px rgba\(0,0,0,0\.12\)' \}\}>/,
    `{/* ── Floating nav pill ── */}
            <div style={{ position: 'fixed', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 50, width: '92%', maxWidth: 1000 }}>
                <div style={{ ...GLASS, borderRadius: 99, padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 0 rgba(255,255,255,0.9) inset, 0 12px 36px rgba(0,0,0,0.1)' }}>`
);
fs.writeFileSync(visPath, visCss);

console.log('Fixed pill layouts!');
