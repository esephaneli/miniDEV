#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  🏢 Mini ChatDev — Multi-Agent AI Yazılım Geliştirme Sistemi  ║
║  Powered by Google Gemini 2.5 Flash (Ücretsiz!)              ║
║  github.com/ZeroCost-Dev-Assistant                           ║
╚══════════════════════════════════════════════════════════════╝

Multi-agent role-play ile yazılım geliştirme simülasyonu.
Her agent Gemini API üzerinden çalışır, Türkçe diyalog kurar,
ve sonuçta çalışan bir Python projesi üretir.

Kullanım:
    python mini_chatdev.py --task "tkinter ile hesap makinesi yap"
    python mini_chatdev.py --task "yılan oyunu yap" --lang tr
    python mini_chatdev.py --task "todo app with CLI" --lang en
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────── Dependencies Check ───────────────────────────

def check_dependencies():
    """Eksik paketleri kontrol et ve kurulum talimatı ver."""
    missing = []
    try:
        from openai import OpenAI
    except ImportError:
        missing.append("openai")
    try:
        from rich.console import Console
    except ImportError:
        missing.append("rich")

    if missing:
        print(f"\n❌ Eksik paketler: {', '.join(missing)}")
        print(f"   Kurulum: pip install {' '.join(missing)}")
        print(f"   veya:    uv pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.live import Live

# ─────────────────────────── Configuration ───────────────────────────

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-2.5-flash"
RPM_LIMIT = 10  # Free tier: 10 requests per minute for 2.5-flash
REQUEST_DELAY = 6.5  # 60/10 = 6s + buffer

console = Console()

# ─────────────────────────── Agent Definitions ───────────────────────────

@dataclass
class Agent:
    """Bir AI ajanını temsil eder."""
    name: str
    role: str
    emoji: str
    color: str
    system_prompt: str

def get_agents(lang: str = "tr") -> dict[str, Agent]:
    """Dil seçimine göre agent'ları döndür."""

    if lang == "tr":
        return {
            "ceo": Agent(
                name="Ahmet (CEO)",
                role="Chief Executive Officer",
                emoji="👔",
                color="bold yellow",
                system_prompt="""Sen bir yazılım şirketinin CEO'susun. Adın Ahmet.
Görevin: Kullanıcının talebini analiz edip net bir ürün tanımı oluşturmak.
- Ürünün ne yapacağını madde madde belirle
- Hedef kullanıcıyı tanımla
- Temel özellikleri listele
- Kısa ve öz ol, gereksiz detaya girme
Yanıtını Türkçe ver."""
            ),
            "cto": Agent(
                name="Zeynep (CTO)",
                role="Chief Technology Officer",
                emoji="🔧",
                color="bold cyan",
                system_prompt="""Sen bir yazılım şirketinin CTO'susun. Adın Zeynep.
Görevin: CEO'nun ürün tanımına göre teknik mimariyi belirlemek.
- Hangi Python kütüphaneleri kullanılacak
- Dosya yapısı nasıl olacak
- Temel sınıflar ve fonksiyonlar neler
- Tek dosya mı çoklu dosya mı karar ver
- Kısa ve öz ol
Yanıtını Türkçe ver."""
            ),
            "programmer": Agent(
                name="Can (Programmer)",
                role="Senior Developer",
                emoji="💻",
                color="bold green",
                system_prompt="""Sen kıdemli bir Python geliştiricisisin. Adın Can.
Görevin: CTO'nun teknik tasarımına göre ÇALIŞAN Python kodu yazmak.

KRİTİK KURALLAR:
- SADECE Python kodu üret, başka bir şey yazma
- Kod EKSIKSIZ ve ÇALIŞIR olmalı
- Tüm import'lar dosyanın başında olmalı
- Her fonksiyonun docstring'i olmalı
- main() fonksiyonu ve if __name__ == "__main__" bloğu olmalı
- Kodun tamamını tek bir ```python ``` bloğu içinde ver
- Yorum satırları Türkçe olsun
- PEP 8 standartlarına uy"""
            ),
            "reviewer": Agent(
                name="Elif (Code Reviewer)",
                role="Senior Code Reviewer",
                emoji="🔍",
                color="bold magenta",
                system_prompt="""Sen kıdemli bir kod review uzmanısın. Adın Elif.
Görevin: Programmer'ın yazdığı kodu inceleyip iyileştirmek.

KRİTİK KURALLAR:
- Kodu çalıştırılabilirlik açısından kontrol et
- Bug varsa düzelt
- Eksik error handling varsa ekle
- Kodun iyileştirilmiş TAMAMI'nı tek bir ```python ``` bloğu içinde ver
- Sadece küçük iyileştirmeler yap, yapıyı değiştirme
- Eğer kod zaten iyi ise, aynı kodu küçük iyileştirmelerle geri ver
- MUTLAKA tam çalışan kod bloğu döndür"""
            ),
            "tester": Agent(
                name="Burak (QA Tester)",
                role="QA Test Engineer",
                emoji="🧪",
                color="bold red",
                system_prompt="""Sen bir QA test mühendisisin. Adın Burak.
Görevin: Kodu analiz edip test raporu oluşturmak.
- Potansiyel bugları listele
- Edge case'leri belirle
- Genel kalite puanı ver (1-10)
- Kısa ve öz ol
Yanıtını Türkçe ver."""
            ),
        }
    else:  # English
        return {
            "ceo": Agent(
                name="Alex (CEO)",
                role="Chief Executive Officer",
                emoji="👔",
                color="bold yellow",
                system_prompt="""You are the CEO of a software company. Your name is Alex.
Your task: Analyze the user's request and create a clear product definition.
- Define what the product will do
- Identify target users
- List core features
- Be concise"""
            ),
            "cto": Agent(
                name="Sarah (CTO)",
                role="Chief Technology Officer",
                emoji="🔧",
                color="bold cyan",
                system_prompt="""You are the CTO of a software company. Your name is Sarah.
Your task: Define technical architecture based on CEO's product definition.
- Which Python libraries to use
- File structure
- Core classes and functions
- Be concise"""
            ),
            "programmer": Agent(
                name="Dev (Programmer)",
                role="Senior Developer",
                emoji="💻",
                color="bold green",
                system_prompt="""You are a senior Python developer. Your name is Dev.
Your task: Write WORKING Python code based on CTO's technical design.

CRITICAL RULES:
- Output ONLY Python code
- Code must be COMPLETE and RUNNABLE
- All imports at the top
- Include docstrings
- Must have main() and if __name__ == "__main__" block
- Put ALL code in a single ```python ``` block
- Follow PEP 8"""
            ),
            "reviewer": Agent(
                name="Eva (Code Reviewer)",
                role="Senior Code Reviewer",
                emoji="🔍",
                color="bold magenta",
                system_prompt="""You are a senior code reviewer. Your name is Eva.
Your task: Review and improve the programmer's code.

CRITICAL RULES:
- Check for runnability
- Fix any bugs
- Add missing error handling
- Return the COMPLETE improved code in a single ```python ``` block
- Only make small improvements, don't change structure
- ALWAYS return a complete working code block"""
            ),
            "tester": Agent(
                name="Max (QA Tester)",
                role="QA Test Engineer",
                emoji="🧪",
                color="bold red",
                system_prompt="""You are a QA test engineer. Your name is Max.
Your task: Analyze the code and create a test report.
- List potential bugs
- Identify edge cases
- Give an overall quality score (1-10)
- Be concise"""
            ),
        }

# ─────────────────────────── Gemini Client ───────────────────────────

class GeminiClient:
    """Gemini API client with rate limiting."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = OpenAI(
            api_key=api_key,
            base_url=GEMINI_BASE_URL,
        )
        self.model = model
        self.last_request_time = 0
        self.total_requests = 0

    def _rate_limit_wait(self):
        """Rate limit'e takılmamak için bekleme."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            wait_time = REQUEST_DELAY - elapsed
            with Progress(
                SpinnerColumn(),
                TextColumn("[dim]⏳ Rate limit bekleniyor... {task.fields[remaining]:.1f}s[/dim]"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("waiting", remaining=wait_time)
                while wait_time > 0:
                    sleep_step = min(0.5, wait_time)
                    time.sleep(sleep_step)
                    wait_time -= sleep_step
                    progress.update(task, remaining=wait_time)

    def chat(self, agent: Agent, user_message: str) -> str:
        """Agent olarak Gemini'ye mesaj gönder."""
        self._rate_limit_wait()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": agent.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=8192,
            )
            self.last_request_time = time.time()
            self.total_requests += 1
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                console.print("[bold red]⚠️  Rate limit aşıldı! 60 saniye bekleniyor...[/bold red]")
                time.sleep(60)
                return self.chat(agent, user_message)
            elif "401" in error_msg:
                console.print("[bold red]❌ API Key geçersiz! .env dosyasını kontrol edin.[/bold red]")
                sys.exit(1)
            else:
                console.print(f"[bold red]❌ API Hatası: {error_msg}[/bold red]")
                sys.exit(1)

# ─────────────────────────── Code Extractor ───────────────────────────

def extract_python_code(text: str) -> Optional[str]:
    """Yanıttan Python kodunu çıkar."""
    # ```python ... ``` bloğunu bul
    patterns = [
        r'```python\s*\n(.*?)```',
        r'```py\s*\n(.*?)```',
        r'```\s*\n(.*?)```',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            if len(code) > 50:  # Gerçek kod mu kontrol et
                return code

    # Eğer kod bloğu yoksa ve tüm metin kod gibi görünüyorsa
    lines = text.strip().split('\n')
    code_lines = [l for l in lines if l.strip().startswith(('import ', 'from ', 'def ', 'class ', '#', 'if __name__'))]
    if len(code_lines) > 3:
        return text.strip()

    return None

# ─────────────────────────── UI Helpers ───────────────────────────

def print_banner():
    """Açılış banner'ını göster."""
    banner = """
[bold white]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🏢 [bold yellow]Mini ChatDev[/bold yellow] — Multi-Agent Yazılım Geliştirme       ║
║   🤖 Powered by [bold cyan]Google Gemini 2.5 Flash[/bold cyan]                  ║
║   💰 [bold green]Tamamen Ücretsiz![/bold green]                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold white]
"""
    console.print(banner)

def print_agent_message(agent: Agent, message: str, is_thinking: bool = False):
    """Agent mesajını göster."""
    title = f"{agent.emoji} {agent.name} — {agent.role}"

    if is_thinking:
        with Progress(
            SpinnerColumn(style=agent.color),
            TextColumn(f"[{agent.color}]{agent.emoji} {agent.name} düşünüyor...[/{agent.color}]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("thinking")
            yield  # Generator olarak kullanılacak
    else:
        panel = Panel(
            Markdown(message),
            title=f"[{agent.color}]{title}[/{agent.color}]",
            border_style=agent.color,
            padding=(1, 2),
        )
        console.print(panel)
        console.print()

def print_code_block(code: str, filename: str = "main.py"):
    """Kodu syntax highlighting ile göster."""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    panel = Panel(
        syntax,
        title=f"[bold green]📄 {filename}[/bold green]",
        border_style="green",
        padding=(1, 1),
    )
    console.print(panel)
    console.print()

def print_phase(phase_num: int, total: int, title: str, emoji: str):
    """Faz başlığını göster."""
    console.print()
    console.print(Rule(f"[bold white] {emoji} Faz {phase_num}/{total}: {title} [/bold white]", style="bright_blue"))
    console.print()

# ─────────────────────────── Pipeline ───────────────────────────

class MiniChatDev:
    """Multi-agent yazılım geliştirme pipeline'ı."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, lang: str = "tr", output_dir: str = "output"):
        self.client = GeminiClient(api_key, model)
        self.agents = get_agents(lang)
        self.lang = lang
        self.output_dir = Path(output_dir)
        self.conversation_log = []
        self.start_time = None

    def _log(self, agent_name: str, phase: str, message: str):
        """Konuşmayı logla."""
        self.conversation_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "phase": phase,
            "message": message,
        })

    def _ask_agent(self, agent_key: str, prompt: str, phase: str) -> str:
        """Agent'a soru sor ve yanıtı göster."""
        agent = self.agents[agent_key]

        # Thinking animasyonu
        with Progress(
            SpinnerColumn(style=agent.color),
            TextColumn(f"[{agent.color}]{agent.emoji} {agent.name} düşünüyor...[/{agent.color}]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("thinking")
            response = self.client.chat(agent, prompt)

        # Yanıtı göster
        title = f"{agent.emoji} {agent.name} — {agent.role}"
        panel = Panel(
            Markdown(response),
            title=f"[{agent.color}]{title}[/{agent.color}]",
            border_style=agent.color,
            padding=(1, 2),
        )
        console.print(panel)
        console.print()

        # Logla
        self._log(agent.name, phase, response)

        return response

    def run(self, task: str, project_name: str = "MyProject") -> Optional[str]:
        """Tüm pipeline'ı çalıştır."""
        self.start_time = time.time()

        print_banner()

        # Proje bilgisi
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column(style="bold cyan")
        info_table.add_column(style="white")
        info_table.add_row("📋 Görev:", task)
        info_table.add_row("📁 Proje:", project_name)
        info_table.add_row("🤖 Model:", self.client.model)
        info_table.add_row("🌐 Dil:", "Türkçe 🇹🇷" if self.lang == "tr" else "English 🇺🇸")
        console.print(Panel(info_table, title="[bold]Proje Bilgileri[/bold]", border_style="bright_blue"))
        console.print()

        # ═══════════════════ FAZ 1: CEO — Ürün Analizi ═══════════════════
        print_phase(1, 5, "Ürün Analizi", "👔")
        ceo_prompt = f"""Kullanıcı şu yazılımı istiyor: "{task}"

Bu talebi analiz et ve şunları belirle:
1. Ürün ne yapacak? (kısa açıklama)
2. Temel özellikler (maddeler halinde)
3. Kullanıcı arayüzü nasıl olacak?
4. Teknik gereksinimler

Kısa ve öz ol."""

        ceo_response = self._ask_agent("ceo", ceo_prompt, "product_analysis")

        # ═══════════════════ FAZ 2: CTO — Teknik Tasarım ═══════════════════
        print_phase(2, 5, "Teknik Tasarım", "🔧")
        cto_prompt = f"""CEO'nun ürün tanımı:

{ceo_response}

Bu ürün için teknik mimariyi tasarla:
1. Kullanılacak Python kütüphaneleri (sadece standart kütüphane + yaygın paketler)
2. Sınıf ve fonksiyon yapısı
3. Dosya yapısı
4. Veri akışı

NOT: Tek bir Python dosyası olarak tasarla. Sadece Python standart kütüphanesi + tkinter/pygame gibi yaygın paketleri kullan."""

        cto_response = self._ask_agent("cto", cto_prompt, "technical_design")

        # ═══════════════════ FAZ 3: Programmer — Kodlama ═══════════════════
        print_phase(3, 5, "Kodlama", "💻")
        programmer_prompt = f"""Kullanıcı talebi: "{task}"

CEO'nun ürün tanımı:
{ceo_response}

CTO'nun teknik tasarımı:
{cto_response}

Bu tasarıma göre TAM ÇALIŞAN Python kodu yaz.

KRİTİK:
- Kodun tamamını tek bir ```python ``` bloğu içinde ver
- Tüm import'lar en üstte
- main() fonksiyonu olmalı
- if __name__ == "__main__" bloğu olmalı
- Hata yönetimi ekle
- Kod EKSIKSIZ olmalı, placeholder veya TODO bırakma"""

        programmer_response = self._ask_agent("programmer", programmer_prompt, "coding")
        code = extract_python_code(programmer_response)

        if not code:
            console.print("[bold red]❌ Programmer kod üretemedi! Tekrar deneniyor...[/bold red]")
            retry_prompt = f"""Önceki yanıtında geçerli Python kodu bulunamadı. 
Lütfen şu talep için eksiksiz Python kodu yaz: "{task}"

SADECE ```python ``` bloğu içinde kod ver, başka hiçbir şey yazma."""
            programmer_response = self._ask_agent("programmer", retry_prompt, "coding_retry")
            code = extract_python_code(programmer_response)

            if not code:
                console.print("[bold red]❌ Kod üretimi başarısız oldu.[/bold red]")
                return None

        console.print("[bold green]✅ Kod başarıyla üretildi![/bold green]")
        print_code_block(code, f"{project_name}.py")

        # ═══════════════════ FAZ 4: Reviewer — Kod İnceleme ═══════════════════
        print_phase(4, 5, "Kod İnceleme", "🔍")
        reviewer_prompt = f"""Şu Python kodunu incele ve iyileştir:

```python
{code}
```

Kontrol listesi:
- Syntax hataları var mı?
- Runtime hataları olabilir mi?
- Error handling yeterli mi?
- Edge case'ler düşünülmüş mü?

İyileştirilmiş kodun TAMAMINI tek bir ```python ``` bloğu içinde ver.
Sadece gerekli düzeltmeleri yap, büyük değişiklik yapma."""

        reviewer_response = self._ask_agent("reviewer", reviewer_prompt, "code_review")
        reviewed_code = extract_python_code(reviewer_response)

        if reviewed_code and len(reviewed_code) > 50:
            code = reviewed_code
            console.print("[bold green]✅ Kod review tamamlandı ve iyileştirildi![/bold green]")
            print_code_block(code, f"{project_name}.py")
        else:
            console.print("[bold yellow]⚠️  Reviewer'dan geçerli kod alınamadı, orijinal kod kullanılıyor.[/bold yellow]")

        # ═══════════════════ FAZ 5: Tester — Test Raporu ═══════════════════
        print_phase(5, 5, "Test & Kalite Raporu", "🧪")
        tester_prompt = f"""Şu Python kodunu test perspektifinden analiz et:

```python
{code}
```

Test raporu oluştur:
1. Genel değerlendirme
2. Potansiyel buglar
3. Edge case'ler
4. Kalite puanı (1-10)
5. Öneri ve tavsiyeler"""

        tester_response = self._ask_agent("tester", tester_prompt, "testing")

        # ═══════════════════ KAYDETME ═══════════════════
        saved_path = self._save_project(project_name, code, task)

        # ═══════════════════ ÖZET ═══════════════════
        self._print_summary(project_name, saved_path, task)

        return code

    def _save_project(self, project_name: str, code: str, task: str) -> Path:
        """Projeyi dosyaya kaydet."""
        # Proje dizini oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.output_dir / f"{project_name}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # Ana kodu kaydet
        code_file = project_dir / f"{project_name.lower()}.py"
        code_file.write_text(code, encoding="utf-8")

        # Conversation log kaydet
        log_file = project_dir / "conversation_log.json"
        log_data = {
            "project_name": project_name,
            "task": task,
            "model": self.client.model,
            "language": self.lang,
            "total_api_calls": self.client.total_requests,
            "timestamp": datetime.now().isoformat(),
            "conversations": self.conversation_log,
        }
        log_file.write_text(json.dumps(log_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # README oluştur
        readme_content = f"""# {project_name}

> 🤖 Bu proje **Mini ChatDev** tarafından otomatik olarak üretilmiştir.

## 📋 Görev
{task}

## 🚀 Çalıştırma
```bash
python {project_name.lower()}.py
```

## 🏗️ Üretim Detayları
- **Model:** {self.client.model}
- **Tarih:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **API Çağrısı:** {self.client.total_requests} istek
- **Dil:** {"Türkçe" if self.lang == "tr" else "English"}
- **Maliyet:** $0.00 (Gemini Free Tier) 🎉

## 📁 Dosyalar
- `{project_name.lower()}.py` — Ana uygulama kodu
- `conversation_log.json` — Agent diyalog geçmişi
- `README.md` — Bu dosya

---
*Mini ChatDev ile ❤️ ile üretildi*
"""
        readme_file = project_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")

        console.print()
        console.print(f"[bold green]💾 Proje kaydedildi: {project_dir}[/bold green]")

        return project_dir

    def _print_summary(self, project_name: str, saved_path: Path, task: str):
        """Final özet tablosunu göster."""
        elapsed = time.time() - self.start_time

        console.print()
        console.print(Rule("[bold white] 📊 Proje Özeti [/bold white]", style="bright_green"))
        console.print()

        summary = Table(show_header=False, box=None, padding=(0, 2))
        summary.add_column(style="bold cyan", min_width=20)
        summary.add_column(style="white")
        summary.add_row("📋 Proje", project_name)
        summary.add_row("🎯 Görev", task[:80] + "..." if len(task) > 80 else task)
        summary.add_row("🤖 Model", self.client.model)
        summary.add_row("📡 API Çağrısı", f"{self.client.total_requests} istek")
        summary.add_row("⏱️  Süre", f"{elapsed:.1f} saniye")
        summary.add_row("💰 Maliyet", "$0.00 🎉")
        summary.add_row("📁 Konum", str(saved_path))

        panel = Panel(
            summary,
            title="[bold green]✅ Proje Başarıyla Tamamlandı![/bold green]",
            border_style="bright_green",
            padding=(1, 2),
        )
        console.print(panel)

        # Çalıştırma talimatı
        console.print()
        run_cmd = f"cd {saved_path} && python {project_name.lower()}.py"
        console.print(Panel(
            f"[bold white]{run_cmd}[/bold white]",
            title="[bold cyan]🚀 Çalıştırmak için[/bold cyan]",
            border_style="cyan",
        ))
        console.print()

# ─────────────────────────── CLI Entry Point ───────────────────────────

def load_api_key() -> str:
    """API key'i environment veya .env dosyasından yükle."""
    # 1. Environment variable
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key

    # 2. .env dosyası
    env_paths = [
        Path(".env"),
        Path("../.env"),
        Path.home() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
                    return v

    # 3. Bulunamadı
    console.print("[bold red]❌ API Key bulunamadı![/bold red]")
    console.print()
    console.print("Şu yöntemlerden birini kullanın:")
    console.print("  1. [cyan]$env:GEMINI_API_KEY = \"your-key\"[/cyan]  (PowerShell)")
    console.print("  2. [cyan]export GEMINI_API_KEY=your-key[/cyan]     (Linux/Mac)")
    console.print("  3. [cyan].env[/cyan] dosyasına [cyan]GEMINI_API_KEY=your-key[/cyan] yazın")
    console.print()
    console.print("🔑 Ücretsiz key almak için: [link]https://aistudio.google.com/apikey[/link]")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="🏢 Mini ChatDev — Multi-Agent AI Yazılım Geliştirme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python mini_chatdev.py --task "tkinter ile hesap makinesi yap"
  python mini_chatdev.py --task "yılan oyunu yap" --name "SnakeGame"
  python mini_chatdev.py --task "todo list CLI app" --lang en
  python mini_chatdev.py --task "pomodoro zamanlayıcı yap" --model gemini-2.0-flash
        """,
    )
    parser.add_argument(
        "--task", "-t",
        required=True,
        help="Yazılım görevi / talebi",
    )
    parser.add_argument(
        "--name", "-n",
        default="MyProject",
        help="Proje adı (varsayılan: MyProject)",
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model (varsayılan: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--lang", "-l",
        choices=["tr", "en"],
        default="tr",
        help="Agent dili (varsayılan: tr)",
    )
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Çıktı dizini (varsayılan: output/)",
    )

    args = parser.parse_args()

    # API Key yükle
    api_key = load_api_key()

    # Pipeline'ı çalıştır
    dev = MiniChatDev(
        api_key=api_key,
        model=args.model,
        lang=args.lang,
        output_dir=args.output,
    )

    try:
        code = dev.run(task=args.task, project_name=args.name)
        if code:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  İptal edildi.[/bold yellow]")
        sys.exit(130)

if __name__ == "__main__":
    main()
