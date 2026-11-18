#!/usr/bin/env python3
"""
Projectify: read a video, audio file, web page, PDF, document or pictures on this computer so Claude can explain it
and turn it into a workflow. Uses whatever is installed (ffmpeg, whisper.cpp, mlx-whisper, openai-whisper,
faster-whisper, yt-dlp, tesseract, Pillow) and says plainly what is missing and how to add it. Standard library only.

  python3 analyse_media.py <file-or-link> --out <folder> [--max-frames 48] [--scene 0.3] [--lang en]

Writes into <folder>: manifest.json (what was found and where), transcript.json and transcript.txt, frames/*.jpg,
sheets/*.jpg (contact sheets with the time of each frame), text.md (a document's or page's text).
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser

VIDEO = {'.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi'}
AUDIO = {'.mp3', '.m4a', '.wav', '.aac', '.ogg', '.flac'}
IMAGE = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.heic'}
TEXT = {'.md', '.txt', '.markdown', '.html', '.htm'}

missing = []
used = []


def have(cmd):
    return shutil.which(cmd) is not None


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def note_missing(tool, why, install):
    missing.append({'tool': tool, 'why': why, 'install': install})


def fmt(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


# ---------- sources ----------
def fetch_page(url, out):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Projectify reader)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        ctype = r.headers.get('content-type', '')
        data = r.read(25_000_000)
    if 'pdf' in ctype or url.lower().endswith('.pdf'):
        p = os.path.join(out, 'source.pdf')
        open(p, 'wb').write(data)
        return {'kind': 'document', 'file': p}
    text, title, images = html_to_markdown(data.decode('utf-8', 'replace'), url)
    open(os.path.join(out, 'text.md'), 'w').write(text)
    return {'kind': 'page', 'name': title or url, 'url': url, 'text_file': 'text.md', 'images': images[:40], 'words': len(text.split())}


class _Html(HTMLParser):
    SKIP = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'svg', 'form'}

    def __init__(self, base):
        super().__init__()
        self.out, self.skip, self.title, self.in_title, self.images, self.base = [], 0, '', False, [], base

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
        if tag == 'title':
            self.in_title = True
        if self.skip:
            return
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self.out.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag in ('p', 'div', 'section', 'article', 'br', 'tr'):
            self.out.append('\n')
        elif tag == 'li':
            self.out.append('\n- ')
        elif tag == 'img' and a.get('src'):
            self.images.append({'url': urllib.parse.urljoin(self.base, a['src']), 'alt': a.get('alt', '')})

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == 'title':
            self.in_title = False

    def handle_data(self, d):
        if self.in_title:
            self.title += d
        elif not self.skip:
            self.out.append(d)


def html_to_markdown(src, base):
    import urllib.parse  # noqa: F401  (used by the parser)
    p = _Html(base)
    p.feed(src)
    text = html.unescape(''.join(p.out))
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text).strip()
    return text, p.title.strip(), p.images


def youtube(url, out):
    if not have('yt-dlp'):
        note_missing('yt-dlp', 'to download the video and its captions', 'brew install yt-dlp  (or: pipx install yt-dlp)')
        return None
    used.append('yt-dlp')
    tmpl = os.path.join(out, 'source.%(ext)s')
    r = run(['yt-dlp', '-f', 'bv*[height<=720]+ba/b[height<=720]/b', '--merge-output-format', 'mp4', '--write-info-json',
             '--write-subs', '--write-auto-subs', '--sub-langs', 'en.*,en', '--sub-format', 'vtt', '-o', tmpl, url])
    vids = [p for p in glob.glob(os.path.join(out, 'source.*')) if os.path.splitext(p)[1] in VIDEO]
    if not vids:
        raise SystemExit(f'yt-dlp could not download it: {r.stderr.strip()[-400:]}')
    info = {}
    for p in glob.glob(os.path.join(out, 'source*.info.json')):
        info = json.load(open(p))
    subs = sorted(glob.glob(os.path.join(out, 'source*.vtt')))
    return {'file': vids[0], 'subs': subs[0] if subs else None, 'name': info.get('title') or url, 'author': info.get('uploader'),
            'description': (info.get('description') or '')[:4000]}


# ---------- video and audio ----------
def probe(path):
    if not have('ffprobe'):
        return {}
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', path])
    try:
        j = json.loads(r.stdout)
    except ValueError:
        return {}
    v = next((s for s in j.get('streams', []) if s.get('codec_type') == 'video'), {})
    return {'seconds': float(j.get('format', {}).get('duration', 0) or 0), 'width': v.get('width'), 'height': v.get('height'),
            'has_audio': any(s.get('codec_type') == 'audio' for s in j.get('streams', []))}


def vtt_to_segments(path):
    segs, cur = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.strip()
        m = re.match(r'(\d+):(\d+):(\d+)[.,](\d+)\s*-->\s*(\d+):(\d+):(\d+)[.,](\d+)', line) or re.match(r'(\d+):(\d+)[.,](\d+)\s*-->', line)
        if m and '-->' in line:
            parts = re.findall(r'(?:(\d+):)?(\d+):(\d+)[.,](\d+)', line)
            def sec(p):
                h, mi, s, ms = p
                return int(h or 0) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000
            cur = {'at': sec(parts[0]), 'to': sec(parts[1]) if len(parts) > 1 else None, 'text': ''}
            segs.append(cur)
        elif cur is not None and line and not line.startswith(('WEBVTT', 'Kind:', 'Language:', 'NOTE')):
            clean = re.sub(r'<[^>]+>', '', line)
            if clean and clean not in cur['text']:
                cur['text'] = (cur['text'] + ' ' + clean).strip()
    # captions repeat lines as they roll: drop segments whose text the previous one already ends with
    out = []
    for s in segs:
        if not s['text']:
            continue
        if out and s['text'].startswith(out[-1]['text']):
            s['text'] = s['text'][len(out[-1]['text']):].strip()
            if not s['text']:
                continue
        out.append(s)
    return out


def srt_to_segments(path):
    segs = []
    blocks = open(path, encoding='utf-8', errors='replace').read().split('\n\n')
    for b in blocks:
        m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', b)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        text = ' '.join(l.strip() for l in b.split('\n')[2:] if l.strip())
        if text:
            segs.append({'at': g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, 'to': g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, 'text': text})
    return segs


def whisper_model():
    env = os.environ.get('WHISPER_MODEL')
    if env and os.path.exists(env):
        return env
    for d in [os.path.expanduser('~/.cache/whisper'), os.path.expanduser('~/.cache/whisper.cpp'), '/opt/homebrew/share/whisper-cpp', '/usr/local/share/whisper-cpp']:
        for name in ['ggml-large-v3-turbo.bin', 'ggml-medium.en.bin', 'ggml-small.en.bin', 'ggml-base.en.bin', 'ggml-base.bin', 'ggml-small.bin']:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def transcribe(video, out, lang):
    wav = os.path.join(out, 'audio.wav')
    if not have('ffmpeg'):
        return None
    run(['ffmpeg', '-y', '-v', 'error', '-i', video, '-vn', '-ar', '16000', '-ac', '1', wav])
    if not os.path.exists(wav) or os.path.getsize(wav) < 1000:
        return None
    base = os.path.join(out, 'whisper')
    # 1. whisper.cpp
    for cli in ['whisper-cli', 'whisper-cpp', 'main']:
        model = whisper_model()
        if have(cli) and model and cli != 'main':
            r = run([cli, '-m', model, '-f', wav, '-osrt', '-of', base, '-l', lang, '-t', str(max(2, (os.cpu_count() or 4) - 2))])
            if os.path.exists(base + '.srt'):
                used.append(f'{cli} ({os.path.basename(model)})')
                return srt_to_segments(base + '.srt')
            print(f'{cli} failed: {r.stderr.strip()[-300:]}', file=sys.stderr)
    # 2. mlx-whisper, openai-whisper
    for cli, args in [('mlx_whisper', ['--output-format', 'srt', '--output-dir', out]), ('whisper', ['--output_format', 'srt', '--output_dir', out, '--model', 'base'])]:
        if have(cli):
            run([cli, wav, '--language', lang] + args)
            srt = os.path.join(out, 'audio.srt')
            if os.path.exists(srt):
                used.append(cli)
                return srt_to_segments(srt)
    # 3. faster-whisper
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = WhisperModel('base', compute_type='int8')
        segs, _ = model.transcribe(wav, language=lang)
        used.append('faster-whisper')
        return [{'at': s.start, 'to': s.end, 'text': s.text.strip()} for s in segs]
    except Exception:
        pass
    # 4. OpenAI's API, when a key is set
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return openai_transcribe(wav, out, key)
    note_missing('a speech-to-text tool', 'to transcribe what is said', 'brew install whisper-cpp, then download a model: '
                 'curl -L -o ~/.cache/whisper/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin  '
                 '(or set OPENAI_API_KEY)')
    return None


def openai_transcribe(wav, out, key):
    import uuid
    chunks = os.path.join(out, 'chunks')
    os.makedirs(chunks, exist_ok=True)
    run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-f', 'segment', '-segment_time', '600', '-c:a', 'libmp3lame', '-b:a', '48k', os.path.join(chunks, 'c%03d.mp3')])
    segs = []
    for i, p in enumerate(sorted(glob.glob(os.path.join(chunks, 'c*.mp3')))):
        boundary = uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode() + open(p, 'rb').read() + f'\r\n--{boundary}--\r\n'.encode()
        req = urllib.request.Request('https://api.openai.com/v1/audio/transcriptions', data=body, headers={'Authorization': f'Bearer {key}', 'Content-Type': f'multipart/form-data; boundary={boundary}'})
        with urllib.request.urlopen(req, timeout=600) as r:
            j = json.load(r)
        for s in j.get('segments', []):
            segs.append({'at': s['start'] + i * 600, 'to': s['end'] + i * 600, 'text': s['text'].strip()})
    used.append('OpenAI whisper-1')
    return segs


def scene_frames(video, out, seconds, max_frames, threshold):
    frames_dir = os.path.join(out, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    r = run(['ffmpeg', '-hide_banner', '-i', video, '-an', '-vf', f"scale=320:-1,select='gt(scene,{threshold})',showinfo", '-f', 'null', '-'])
    times = [float(t) for t in re.findall(r'pts_time:([0-9.]+)', r.stderr)]
    # cover gaps: a frame at least every 45 seconds, and the opening
    times = sorted(set([0.5] + times))
    filled = []
    for t in times:
        while filled and t - filled[-1] > 45:
            filled.append(filled[-1] + 30)
        filled.append(t)
    times = [t for t in filled if t < max(1, seconds - 0.5)]
    # keep them apart and under the cap, evenly
    spaced = []
    for t in times:
        if not spaced or t - spaced[-1] >= 2.0:
            spaced.append(t)
    if len(spaced) > max_frames:
        step = len(spaced) / max_frames
        spaced = [spaced[int(i * step)] for i in range(max_frames)]
    frames = []
    for i, t in enumerate(spaced):
        p = os.path.join(frames_dir, f'f{i + 1:03d}.jpg')
        # a beat after the cut, so the frame is not mid-transition
        run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{t + 0.4:.2f}', '-i', video, '-frames:v', '1', '-vf', 'scale=960:-2', '-q:v', '5', p])
        if os.path.exists(p):
            frames.append({'id': f'f{i + 1}', 'at': round(t, 2), 'file': os.path.relpath(p, out)})
    used.append(f'ffmpeg scene detection ({len(times)} cuts, kept {len(frames)})')
    return frames


def contact_sheets(frames, out, per=20):
    try:
        from PIL import Image, ImageDraw  # type: ignore
    except Exception:
        note_missing('Pillow', 'to make contact sheets (Claude can still open the frames one by one)', 'python3 -m pip install --user Pillow')
        return []
    os.makedirs(os.path.join(out, 'sheets'), exist_ok=True)
    sheets = []
    cols, w = 4, 360
    for s in range(0, len(frames), per):
        chunk = frames[s:s + per]
        ims = [Image.open(os.path.join(out, f['file'])).convert('RGB') for f in chunk]
        h = int(w * ims[0].height / ims[0].width)
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * w, rows * (h + 24)), 'white')
        d = ImageDraw.Draw(sheet)
        for i, (im, f) in enumerate(zip(ims, chunk)):
            x, y = (i % cols) * w, (i // cols) * (h + 24)
            sheet.paste(im.resize((w, h)), (x, y + 24))
            d.text((x + 6, y + 6), f"{f['id']}  {fmt(f['at'])}", fill='black')
        p = os.path.join(out, 'sheets', f'sheet_{s // per + 1:02d}.jpg')
        sheet.save(p, quality=78)
        sheets.append(os.path.relpath(p, out))
    return sheets


def ocr(frames, out):
    if not have('tesseract'):
        note_missing('tesseract', 'to read text on screen (settings, prompts, menus)', 'brew install tesseract')
        return
    used.append('tesseract')
    for f in frames:
        r = run(['tesseract', os.path.join(out, f['file']), '-', '--psm', '11'])
        words = [w for w in re.split(r'\s+', r.stdout) if len(w) > 2 and re.search(r'[A-Za-z]{3}', w)]
        if len(words) >= 3:
            f['text'] = ' '.join(words)[:600]


def document(path, out):
    ext = os.path.splitext(path)[1].lower()
    text = ''
    if ext == '.pdf':
        if have('pdftotext'):
            run(['pdftotext', '-layout', path, os.path.join(out, 'text.md')])
            used.append('pdftotext')
            text = open(os.path.join(out, 'text.md')).read()
        else:
            note_missing('pdftotext', 'to read the PDF\'s text (Claude can read the PDF itself instead)', 'brew install poppler')
    elif ext == '.docx':
        import zipfile
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml').decode('utf-8', 'replace')
        xml = re.sub(r'</w:p>', '\n', xml)
        text = html.unescape(re.sub(r'<[^>]+>', '', xml))
        used.append('docx reader')
    elif ext in ('.html', '.htm'):
        text, _, _ = html_to_markdown(open(path, encoding='utf-8', errors='replace').read(), 'file://' + path)
    else:
        text = open(path, encoding='utf-8', errors='replace').read()
    if text:
        open(os.path.join(out, 'text.md'), 'w').write(text)
    return {'kind': 'document', 'text_file': 'text.md' if text else None, 'words': len(text.split())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-frames', type=int, default=48)
    ap.add_argument('--scene', type=float, default=0.3)
    ap.add_argument('--lang', default='en')
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    src = a.source
    manifest = {'source': {'input': src}}
    video = None
    subs = None
    if re.match(r'^https?://', src):
        if re.search(r'(youtube\.com|youtu\.be)/', src):
            y = youtube(src, out)
            manifest['source'].update({'kind': 'youtube', 'url': src})
            if y:
                video, subs = y['file'], y['subs']
                manifest['source'].update({'name': y['name'], 'author': y['author'], 'description': y['description']})
        else:
            manifest['source'].update(fetch_page(src, out))
            if manifest['source'].get('kind') == 'document':
                manifest['source'].update(document(manifest['source']['file'], out))
    else:
        path = os.path.abspath(os.path.expanduser(src))
        if not os.path.exists(path):
            raise SystemExit(f'Not found: {path}')
        ext = os.path.splitext(path)[1].lower()
        manifest['source'].update({'name': os.path.basename(path), 'path': path, 'bytes': os.path.getsize(path)})
        if ext in VIDEO or ext in AUDIO:
            video = path
            manifest['source']['kind'] = 'video' if ext in VIDEO else 'audio'
        elif ext in IMAGE:
            manifest['source']['kind'] = 'images'
            manifest['frames'] = [{'id': 'f1', 'file': path}]
        else:
            manifest['source'].update(document(path, out))
    if video:
        if not have('ffmpeg'):
            note_missing('ffmpeg', 'to read video and audio', 'brew install ffmpeg')
        else:
            meta = probe(video)
            manifest['source'].update({k: v for k, v in meta.items() if v is not None})
            segs = vtt_to_segments(subs) if subs else None
            if segs:
                used.append('captions')
            elif meta.get('has_audio', True):
                segs = transcribe(video, out, a.lang)
            if segs:
                json.dump(segs, open(os.path.join(out, 'transcript.json'), 'w'))
                lines, last = [], -999
                for s in segs:
                    if s['at'] - last >= 30:
                        lines.append(f"\n[{fmt(s['at'])}] ")
                        last = s['at']
                    lines.append(s['text'] + ' ')
                open(os.path.join(out, 'transcript.txt'), 'w').write(''.join(lines).strip())
                manifest['transcript'] = {'file': 'transcript.json', 'text_file': 'transcript.txt', 'segments': len(segs), 'words': sum(len(s['text'].split()) for s in segs)}
            if manifest['source'].get('kind') != 'audio':
                frames = scene_frames(video, out, meta.get('seconds') or 0, a.max_frames, a.scene)
                ocr(frames, out)
                manifest['frames'] = frames
                manifest['sheets'] = contact_sheets(frames, out)
    manifest['used'] = used
    manifest['missing'] = missing
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    s = manifest['source']
    print(f"Read: {s.get('name', src)} ({s.get('kind', '?')})")
    if s.get('seconds'):
        print(f"Length: {fmt(s['seconds'])}")
    if manifest.get('transcript'):
        print(f"Transcript: {manifest['transcript']['words']} words → {os.path.join(out, 'transcript.txt')}")
    if manifest.get('frames'):
        print(f"Frames: {len(manifest['frames'])} → {os.path.join(out, 'frames')}")
    if manifest.get('sheets'):
        print(f"Contact sheets (open these first): " + ', '.join(os.path.join(out, p) for p in manifest['sheets']))
    if s.get('text_file'):
        print(f"Text: {s.get('words', 0)} words → {os.path.join(out, s['text_file'])}")
    print('Used: ' + (', '.join(used) or 'nothing'))
    for m in missing:
        print(f"Missing {m['tool']} ({m['why']}). Add it with: {m['install']}")
    print(f"Manifest: {os.path.join(out, 'manifest.json')}")


if __name__ == '__main__':
    main()
