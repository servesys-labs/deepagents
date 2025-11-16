# 🥑 AvocadoDB Auto-Start for DeepAgents

**Zero-config deterministic context retrieval**

## 🚀 Quick Start (Auto-Everything)

```bash
# Enable auto-start
export AVOCADODB_AUTO_START=true

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Start DeepAgents - AvocadoDB starts automatically!
deepagents
```

That's it! AvocadoDB will:
- ✅ Auto-install binary (first time only)
- ✅ Auto-start server in background
- ✅ Auto-ingest current directory
- ✅ Auto-stop server on exit

---

## 📖 How It Works

### **First Time Use:**
```bash
export AVOCADODB_AUTO_START=true
deepagents

# Output:
🥑 Installing AvocadoDB...
   Cloning repository...
   Building (this may take 2-3 minutes)...
✅ Installed to /Users/you/.avocadodb/avocado-server

🥑 Starting AvocadoDB server...
✅ Server started

🥑 Auto-ingesting /path/to/your/project...
✅ Auto-ingested 8 items

Welcome to DeepAgents! Now with deterministic context retrieval.
```

### **Every Other Time:**
```bash
export AVOCADODB_AUTO_START=true
deepagents

# Output:
🥑 Starting AvocadoDB server...
✅ Server started

Welcome to DeepAgents!
```

**Server automatically stops when you exit DeepAgents.** ✨

---

## 🎯 What Gets Auto-Ingested

On first start in a directory, AvocadoDB automatically ingests:
- `docs/` directory
- `README.md`
- All `*.md` files
- `src/` directory (if exists)

**Max 10 paths** to keep startup fast.

---

## ⚙️ Configuration

### **Environment Variables:**

```bash
# Enable/disable auto-start (default: false)
export AVOCADODB_AUTO_START=true

# Custom server URL (default: http://localhost:8765)
export AVOCADODB_URL="http://localhost:9000"
```

### **Manual Control:**

Prefer manual control? Don't set `AVOCADODB_AUTO_START`:

```bash
# Terminal 1: Start server manually
avocado-server

# Terminal 2: Start DeepAgents
deepagents
```

---

## 🔍 Binary Installation Locations

Auto-installer checks these locations (in order):

1. `./target/release/avocado-server` (current project)
2. `../target/release/avocado-server` (parent directories)
3. `~/.avocadodb/avocado-server` (auto-installed)
4. `/usr/local/bin/avocado-server` (system-wide)

If not found, automatically installs to `~/.avocadodb/`

---

## 💡 Usage Examples

### **Auto Mode (Recommended):**
```bash
export AVOCADODB_AUTO_START=true
export ANTHROPIC_API_KEY="sk-ant-..."
deepagents

# In REPL:
You: Search the codebase for authentication details

# Agent automatically uses AvocadoDB:
🥑 avocado_compile_context
   Query: authentication details
   Token budget: 8000
   ✅ Deterministic retrieval
```

### **Manual Mode:**
```bash
# No auto-start
deepagents

# AvocadoDB tool still available
# Shows helpful install message if server not running
```

---

## 🛠️ Troubleshooting

### **Auto-install fails:**
```bash
# Install manually:
git clone https://github.com/servesys-labs/avacadodb
cd avacadodb
cargo build --release

# Binary will be at: ./target/release/avocado-server
```

### **Server won't start:**
```bash
# Check if port 8765 is in use:
lsof -i :8765

# Use different port:
export AVOCADODB_URL="http://localhost:9000"
```

### **Want to re-ingest:**
```bash
# Manual ingest:
avocado ingest ./docs --recursive
```

---

## 📊 Comparison

| Feature | Manual | Auto-Start |
|---------|--------|------------|
| **Setup** | 5 steps | 1 command |
| **Startup time** | Manual | 2-3 sec |
| **Auto-ingest** | Manual | Automatic |
| **Server cleanup** | Manual | Automatic |
| **Developer experience** | 😐 Okay | 🚀 Excellent |

---

## 🎁 Benefits

**Before (Manual):**
```bash
# Terminal 1
git clone https://github.com/servesys-labs/avacadodb
cd avacadodb
cargo build --release
./target/release/avocado-server &

# Terminal 2
./target/release/avocado ingest docs/ --recursive

# Terminal 3
deepagents
```

**After (Auto):**
```bash
export AVOCADODB_AUTO_START=true
deepagents
```

**60 seconds → 5 seconds!** ⚡

---

## 🚀 Ready to Use

Auto-start is available in this fork:
- **Fork**: https://github.com/servesys-labs/deepagents
- **Branch**: `feat/avocadodb-integration`

```bash
git clone https://github.com/servesys-labs/deepagents
cd deepagents
git checkout feat/avocadodb-integration
cd libs/deepagents-cli
pip install -e .

export AVOCADODB_AUTO_START=true
deepagents
```

**Zero-config deterministic retrieval is here!** 🥑🤖
