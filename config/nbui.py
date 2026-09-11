"""Barras de progresso de uma linha para o notebook (Colab).

Cada barra ocupa UMA linha que se atualiza no lugar, em vez de imprimir
uma linha nova por atualizacao. Usa ipywidgets quando disponivel e cai
para \r no terminal.
"""
import os, sys, time, shutil, subprocess, threading, urllib.request

try:
    import ipywidgets as W
    from IPython.display import display
    _HAS_W = True
except Exception:
    _HAS_W = False


def _human(n):
    if n is None or n < 0:
        return '?'
    for u in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f'{n:.0f}{u}' if u == 'B' else f'{n:.1f}{u}'
        n /= 1024
    return f'{n:.1f}PB'


class Bar:
    """Barra unica. total=None => modo indeterminado (spinner de texto)."""

    def __init__(self, label, total=None, unit='B'):
        self.label, self.total, self.unit = label, total, unit
        self.n, self.t0, self.closed = 0, time.time(), False
        if _HAS_W:
            self.pb = W.FloatProgress(value=0, min=0, max=(total or 1),
                                      layout=W.Layout(width='260px'))
            self.tx = W.HTML()
            self.box = W.HBox([self.pb, self.tx])
            display(self.box)
        self._render()

    def _text(self):
        el = time.time() - self.t0
        if self.total:
            pct = 100 * self.n / self.total
            rate = self.n / el if el > 0 else 0
            eta = (self.total - self.n) / rate if rate > 0 else 0
            if self.unit == 'B':
                det = f'{_human(self.n)}/{_human(self.total)} · {_human(rate)}/s · ETA {int(eta)}s'
            else:
                det = f'{self.n}/{self.total} · ETA {int(eta)}s'
            return f'{pct:5.1f}%', f'{self.label} — {det}'
        det = f'{_human(self.n)} · {int(el)}s' if self.unit == 'B' else f'{int(el)}s'
        return '', f'{self.label} — {det}'

    def _render(self):
        pct, txt = self._text()
        if _HAS_W:
            if self.total:
                self.pb.max = self.total
                self.pb.value = self.n
            else:
                self.pb.value = self.pb.max  # barra cheia = indeterminado
            self.tx.value = f'<code>{pct} {txt}</code>'
        else:
            sys.stdout.write('\r' + (pct + ' ' + txt)[:110].ljust(110))
            sys.stdout.flush()

    def update(self, n=None, add=None, total=None):
        if total is not None:
            self.total = total
        if add is not None:
            self.n += add
        if n is not None:
            self.n = n
        self._render()

    def close(self, msg=None, ok=True):
        if self.closed:
            return
        self.closed = True
        el = int(time.time() - self.t0)
        final = msg or f'{self.label} — concluido em {el}s'
        mark = 'ok' if ok else 'FALHOU'
        if _HAS_W:
            self.pb.value = self.pb.max
            self.pb.bar_style = 'success' if ok else 'danger'
            self.tx.value = f'<code>[{mark}] {final}</code>'
        else:
            sys.stdout.write('\r' + f'[{mark}] {final}'[:110].ljust(110) + '\n')
            sys.stdout.flush()


def download(url, dest, label=None, headers=None):
    """Baixa com barra de uma linha. Retoma parcial via Range. True se ok."""
    label = label or os.path.basename(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + '.part'
    done = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    hd = {'User-Agent': 'Mozilla/5.0'}
    if headers:
        hd.update(headers)
    if done:
        hd['Range'] = f'bytes={done}-'
    bar = Bar(label, total=None)
    try:
        rq = urllib.request.Request(url, headers=hd)
        with urllib.request.urlopen(rq, timeout=120) as r:
            cl = r.headers.get('Content-Length')
            total = (int(cl) + done) if cl else None
            bar.update(n=done, total=total)
            mode = 'ab' if done and r.status == 206 else 'wb'
            if mode == 'wb':
                done = 0
                bar.update(n=0)
            last = 0
            with open(tmp, mode) as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if time.time() - last > 0.3:
                        bar.update(n=done)
                        last = time.time()
        os.replace(tmp, dest)
        bar.update(n=done)
        bar.close(f'{label} — {_human(done)}')
        return True
    except Exception as e:
        bar.close(f'{label} — erro: {str(e)[:60]}', ok=False)
        return False


def run(cmd, label, cwd=None, timeout=None):
    """Roda comando mostrando so uma barra + ultima linha util do log."""
    bar = Bar(label, total=None)
    buf = []
    try:
        p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            line = line.rstrip()
            if line:
                buf.append(line)
                bar.label = f'{label} · {line[:60]}'
                bar.update(add=len(line))
        p.wait(timeout=timeout)
        ok = p.returncode == 0
        bar.label = label
        bar.close(f'{label} — rc={p.returncode}', ok=ok)
        if not ok:
            for l in buf[-12:]:
                print('   |', l)
        return ok
    except Exception as e:
        bar.close(f'{label} — {str(e)[:60]}', ok=False)
        return False


class Steps:
    """Barra de progresso geral de uma celula (passo N de M)."""

    def __init__(self, total, label='Progresso'):
        self.bar = Bar(label, total=total, unit='it')
        self.label = label

    def step(self, name):
        self.bar.label = f'{self.label}: {name}'
        self.bar.update(add=1)

    def close(self):
        self.bar.close(f'{self.label} — {self.bar.n}/{self.bar.total} concluido')
