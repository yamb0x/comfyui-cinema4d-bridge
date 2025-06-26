# Quick Setup Reference - comfy2c4d

## 🚀 Windows Setup Commands

### **New Installation**
```bash
setup_windows_env.bat     # Complete Windows environment setup
```

### **Quick Fixes**
```bash
fix_dependencies.bat      # Fix missing PySide6/qasync/loguru
diagnose_setup.bat        # Check environment health
```

### **Alternative Options**
```bash
setup_simple.bat          # Simple, clean setup
install_dependencies.bat  # Full dependency installer
```

### **Launch Application**
```bash
launch.bat                # Start the application
```

## 🔍 Common Issues → Solutions

| Issue | Command | Description |
|-------|---------|-------------|
| Unix paths in venv | `setup_windows_env.bat` | Recreates venv with Windows paths |
| Missing PySide6 | `fix_dependencies.bat` | Installs missing packages |
| App won't start | `diagnose_setup.bat` | Identifies specific problems |
| Complete rebuild | `setup_simple.bat` | Clean slate installation |

## ⚠️ Important Notes

### **Cloud Sync Warning**
- **Never sync `venv/` directory** with Dropbox/OneDrive
- Causes path corruption and dependency issues
- Move project to local drive: `C:\dev\comfy-to-c4d\`

### **Environment Health Check**
Run `diagnose_setup.bat` to verify:
- ✅ Python installation
- ✅ Virtual environment paths (Windows vs Unix)
- ✅ Required dependencies
- ✅ File structure integrity

### **Settings Dialog (Fixed 2025-01-16)**
- All settings now functional (not just UI placeholders)
- Accent color applies immediately
- Auto-save creates real project backups
- Console settings connect to actual console
- Reset to defaults clears all stored settings

## 🎯 Success Criteria

After setup, verify:
```bash
venv\Scripts\python.exe -c "import PySide6; print('✅ PySide6 OK')"
venv\Scripts\python.exe -c "import qasync; print('✅ qasync OK')"
venv\Scripts\python.exe -c "import loguru; print('✅ loguru OK')"
```

Should output:
```
✅ PySide6 OK
✅ qasync OK  
✅ loguru OK
```

## 📞 If All Else Fails

1. **Close all Python processes**
2. **Delete `venv/` directory completely**
3. **Run `setup_simple.bat`**
4. **Exclude `venv/` from cloud sync**
5. **Use `launch.bat` to start**

*This should resolve 99% of setup issues.*