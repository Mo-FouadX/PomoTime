# PomoTime — Professional Pomodoro Focus Timer

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5.0%2B-green.svg)](https://www.pyqt.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)](https://github.com/Mo-FouadX/PomoTime)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](.github/workflows/build.yml)

---

## English

### 🎯 A Professional, Native Pomodoro Timer for Focus Management

**PomoTime** is a polished, bilingual (English/Arabic) desktop application built with Python 3 and PyQt6 that helps students and professionals manage focus sessions using the proven Pomodoro technique. It is **100% free**, has no accounts, no telemetry, no ads, and stores everything locally on your machine.

Designed for privacy and performance, PomoTime relies entirely on native system tools and pure-Python audio synthesis — no external multimedia dependencies.

**Currently built and supported for Linux** (`.AppImage`, `.deb`, and source). Windows/macOS support is planned.

---

### ✨ Key Features

| Category | Features |
|----------|----------|
| **Focus Timers** | Focus / Short Break / Long Break sessions, fully customizable durations, automatic cycle logic (long break every N cycles). |
| **Session Queue** | Multi-block planner — build your own sequence of focus blocks and breaks; timer advances automatically; reorder, delete, quick-add patterns. |
| **Presets** | Classic Pomodoro (25/5/20 ×4), Deep Work (50/10/30 ×2), Quick Sprint (15/3/10 ×4), Custom Queue. |
| **Daily Goal** | Set a daily focus target; progress bar and midnight reset; all-time totals preserved. |
| **Statistics** | Total focus time, completed cycles, breaks taken, productivity score (0–100), recent-session log, CSV export. |
| **UI/UX** | 4 themes (default, forest, midnight, sunset), floating mini-mode (always on top), system tray, keyboard shortcuts. |
| **Bilingual / RTL** | Instant English ↔ Arabic switch; full interface translation; correct RTL layout for Arabic. |
| **Sounds** | Soft synthesized chimes (click, start focus, start break, alert) — pure Python, no audio files needed. |

---

### 🎓 Built for Students (Free)

PomoTime helps students solve two problems at once: **distraction during study** and **disorganized study time**.

- **Study Subject Planner**: Add each subject (e.g. "Physics — Unit 3") and how many focus blocks it needs. Mark subjects complete as you finish them.
- **Strict Focus Mode**: Locks the app on the timer screen while you study — no switching tabs, no distractions until the timer ends.
- **Weekly Study Stats**: Focus hours per subject this week, weekly goal, and a consecutive-day study streak to build a habit.
- **Achievements / Badges**: Unlock badges like "First Session", "3-Day Streak", "7-Day Streak", "5-Hour Day", "10-Hour Week" to stay motivated.
- **CSV Export**: Export your session history and weekly stats for your own records.

Everything is saved locally — no sign-up, no internet required after installation.

---

### 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Mo-FouadX/PomoTime.git
cd PomoTime

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the application
python3 -m pomotime.main
```

**Requirements:** Python 3.10+, PyQt6 >= 6.5.0. No extra multimedia packages.

---

### ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Start / Pause timer |
| `R` | Reset current session |
| `S` | Skip current stage / queue block |
| `M` | Toggle Floating Mini-Mode |

---

### 📦 Building & Distribution

- **AppImage**: Built automatically by GitHub Actions; download from the [Releases](https://github.com/Mo-FouadX/PomoTime/releases) page or build with `linuxdeploy` + `appimagetool`.
- **.deb Package**: Built by GitHub Actions; download from Releases or build with `dpkg-deb` from the CI pipeline.
- **Source**: `pip install -r requirements.txt && python3 -m pomotime.main`

---

### 🧪 Running Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests cover the session queue, settings storage, translations, and themes. CI runs them on every push and pull request.

---

### 🗣️ العربية

## pomotime — مؤقت بومودورو احترافي للتركيز

**بوموتايم** تطبيق سطح مكتب احترافي ثنائي اللغة (الإنجليزية/العربية) مبني بلغة بايثون 3 و PyQt6، يساعد الطلاب والمهنيين على إدارة جلسات التركيز باستخدام تقنية بومودورو المجربة. التطبيق **مجاني بالكامل**، لا يحتاج حسابات، لا contient تتبع، لا إعلانات، وكل شيء يُحفظ محليًا على جهازك.

مصمم للخصوصية والأداء، يعتمد بوموتايم بالكامل على أدوات النظام الأصلية وتوليد الصوت ببايثون الخالص — بدون اعتماديات وسائط خارجية.

**مدعوم حاليًا لنظام لينكس** (`.AppImage`, `.deb`, والمصدر). دعم ويندوز/ماك مخطط للمستقبل.

---

### ✨ الميزات الأساسية

| القسم | الميزات |
|-------|---------|
| **مؤقتات التركيز** | جلسات تركيز / استراحة قصيرة / استراحة طويلة، مدة قابلة للتخصيص بالكامل، منطق دورات تلقائي (استراحة طويلة كل N دورات). |
| **جدول الجلسات** | مخطط متعدد الكتل —ابنِ تسلسلًا خاصًا من كتل التركيز والاستراحات؛ يتقدم المؤقت تلقائيًا؛ إعادة ترتيب، حذف، إضافة سريعة لأنماط. |
| **الأنماط الجاهزة** | بومودورو كلاسيكي (25/5/20 ×4)، عمل عميق (50/10/30 ×2)، سباق سريع (15/3/10 ×4)، جدول مخصص. |
| **الهدف اليومي** | حدد هدف تركيز يومي؛ شريط تقدم وإعادة ضبط عند منتصف الليل؛ الإجماليات تُحفظ دائمًا. |
| **الإحصائيات** | إجمالي وقت التركيز، الدورات المكتملة، الاستراحات، درجة إنتاجية (0–100)، سجل الجلسات الأخيرة، تصدير CSV. |
| **الواجهة وال تجربة المستخدم** | 4 سمات (افتراضي، غابة، منتصف الليل، غروب)، وضع عائم مصغر (أعلى الجميع)، صينية النظام، اختصارات لوحة المفاتيح. |
| **ثنائي اللغة / RTL** | تبديل فوري بين الإنجليزية والعربية؛ ترجمة كاملة للواجهة؛ تخطيط RTL صحيح للعربية. |
| **الأصوات** | نغمات ناعمة مُولدة بالبايثون (ضغط، بدء تركيز، بدء استراحة، تنبيه) — بايثون خالص، لا حاجة لملفات صوتية. |

---

### 🎓 مصمم للطلاب (مجاني)

يساعد بوموتايم الطلاب على حل مشكلتين في آن واحد: **التشتيت أثناء المذاكرة** و**عدم تنظيم وقت المذاكرة**.

- **مخطط مواد المذاكرة**: أضف كل مادة (مثلاً "فيزياء — الوحدة 3") وعدد جلسات التركيز التي تحتاجها. اجعل المواد مكتملة عند انتهائك منها.
- **وضع التركيز الصارم**: يقفل التطبيق على شاشة التركيز أثناء المذاكرة — بدون switching بين التبويبات، بدون تشتيت حتى ينتهي المؤقت.
- **إحصائيات أسبوعية**: ساعات تركيز لكل مادة هذا الأسبوع، هدف أسبوعي، وسلسلة أيام متواصلة لبناء عادة المذاكرة.
- **الإنجازات والشارات**: افتح شارات مثل "جلسة أولى"، "سلسلة 3 أيام"، "سلسلة 7 أيام", "5 ساعات يوم"، "10 ساعات أسبوع" لتحفيزك على الاستمرار.
- **تصدير CSV**: صدر سجل جلساتك وإحصائياتك الأسبوعية لسجلاتك الشخصية.

كل شيء يُحفظ محليًا — بدون تسجيل، بدون إنترنت بعد التثبيت.

---

### 🚀 البدء السريع

```bash
# استنسخ المستودع
git clone https://github.com/Mo-FouadX/PomoTime.git
cd PomoTime

# ثبّت المتطلبات
pip install --upgrade pip
pip install -r requirements.txt

# شغّل التطبيق
python3 -m pomotime.main
```

**المتطلبات:** بايثون 3.10+، PyQt6 >= 6.5.0. لا حاجة لحزم وسائط إضافية.

---

### ⌨️ اختصارات لوحة المفاتيح

| المفتاح | العملية |
|--------|---------|
| `Space` | بدء / إيقاف مؤقت |
| `R` | إعادة ضبط الجلسة الحالية |
| `S` | تجاوز المرحلة الحالية / كتلة الجدول |
| `M` | تبديل وضع العائم المصغر |

---

### 📦 البناء والتوزيع

- **AppImage**: يبنيه GitHub Actions تلقائيًا؛ حمله من صفحة [الإصدارات](https://github.com/Mo-FouadX/PomoTime/releases) أو بنِّه باستخدام `linuxdeploy` + `appimagetool`.
- **حزمة .deb**: تبنيه GitHub Actions؛ حمله من الإصدارات أو بنِّه باستخدام `dpkg-deb` من خط construcción.
- **المصدر**: `pip install -r requirements.txt && python3 -m pomotime.main`

---

### 🧪 تشغيل الاختبارات

```bash
python3 -m unittest discover -s tests -v
```

تغطي الاختبارات جدول الجلسات، تخزين الإعدادات، الترجمات، والسمات. يُشغل CI الاختبارات عند كل push و pull request.

---

### 📄 License

**PomoTime** is released under the MIT License. See the accompanying [LICENSE](LICENSE) file.

**بوموتايم** صدر برخصة MIT. راجع ملف [LICENSE](LICENSE) المرفق.

---

<div align="center">

Built with Python 3 & PyQt6 • Powered by native system tools • No external multimedia dependencies • **Free for students and everyone**

مبني ببايثون 3 و PyQt6 • مدعوم بأدوات النظام الأصلية • بدون وسائط خارجية • **مجاني للطلاب والجميع**

</div>
