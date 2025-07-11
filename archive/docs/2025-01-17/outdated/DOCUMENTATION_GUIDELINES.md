# Documentation Guidelines for ComfyUI to C4D Bridge

## 🚫 Core Rule: NO New Files Without Approval

**CRITICAL**: Do NOT create new .md files. Update existing documentation instead.

## 📁 Documentation Structure

### Primary Documentation Files
1. **`README.md`** - User-facing documentation
   - Installation instructions
   - Basic usage guide
   - Feature overview
   
2. **`CLAUDE.md`** - AI Development Guidelines
   - Development notes and reminders
   - Current project state
   - Critical warnings and patterns
   
3. **`docs/development/DEVELOPER_GUIDE.md`** - Technical Documentation
   - Architecture overview
   - API references
   - Code patterns and conventions
   
4. **`docs/development/FIXES_HISTORY.md`** - All Fixes in One Place
   - Date-stamped entries
   - Issue description → Solution
   - Searchable fix database

## 📝 Documentation Rules

### When Adding New Information

1. **Feature Documentation**
   ```markdown
   <!-- In DEVELOPER_GUIDE.md -->
   ## New Feature Name
   - Description
   - Implementation details
   - Usage examples
   ```

2. **Bug Fixes**
   ```markdown
   <!-- In FIXES_HISTORY.md -->
   ## 2025-01-09: Settings Dialog Crash
   **Issue**: Dialog crashes when opening settings
   **Cause**: Widget scope issue
   **Solution**: Store widgets on dialog object, not self
   **Files Modified**: src/ui/widgets.py
   ```

3. **API Changes**
   ```markdown
   <!-- In DEVELOPER_GUIDE.md under API Reference -->
   ### Cinema4D Object Creation
   - Updated constants mapping
   - New creation patterns
   ```

## 🔍 Before Creating Any Documentation

1. **Search existing files** for related content
2. **Find the most appropriate section** to update
3. **Add to existing content** rather than creating new files
4. **Use clear section headers** for easy navigation

## ❌ What NOT to Do

- ❌ Create `FEATURE_X_IMPLEMENTATION.md`
- ❌ Create `BUG_FIX_Y.md`
- ❌ Create temporary documentation files
- ❌ Duplicate information across multiple files

## ✅ What TO Do

- ✅ Update relevant sections in existing docs
- ✅ Keep fixes in FIXES_HISTORY.md with dates
- ✅ Add new features to DEVELOPER_GUIDE.md
- ✅ Update README.md for user-facing changes

## 📋 Documentation Checklist

Before documenting:
- [ ] Have I searched existing documentation?
- [ ] Am I updating the right file?
- [ ] Is this the most logical place for this information?
- [ ] Am I avoiding file duplication?

## 🎯 Goal

Maintain a clean, searchable, and organized documentation structure without file sprawl.