# GitHub Setup Guide

## 🔐 Authentication Setup

### Personal Access Token (PAT)

Your GitHub Personal Access Token has been configured for this repository. The token is stored in Git's credential manager for secure access.

### Token Information
- **Token Purpose**: Repository access for comfyui-cinema4d-bridge
- **Permissions**: repo (full control of private repositories)
- **Created**: Previously generated
- **Status**: Active and working

### Using the Token

The token has been configured with Git's credential helper, so you shouldn't need to enter it again for normal operations.

#### Manual Push (if needed)
```bash
git push https://yamb0x:YOUR_TOKEN@github.com/yamb0x/comfyui-cinema4d-bridge.git main
```

### Security Best Practices

1. **Never commit tokens to the repository**
   - The `.claude/` directory is now in `.gitignore`
   - Always check commits for sensitive data before pushing

2. **Token Storage**
   - Git credential helper is configured to store credentials securely
   - Token is cached for future use

3. **Token Rotation**
   - Rotate tokens periodically for security
   - Delete old tokens after creating new ones

### Common Git Commands

```bash
# Check remote URL
git remote -v

# Pull latest changes
git pull origin main

# Check status
git status

# Add all changes
git add -A

# Commit with message
git commit -m "Your commit message"

# Push to GitHub
git push origin main
```

### Troubleshooting

#### Authentication Failed
If you get authentication errors:
1. Check token hasn't expired on GitHub
2. Ensure token has correct permissions
3. Try manual push with token in URL

#### Secret Detection
If GitHub blocks push due to secrets:
1. Remove sensitive files from commit
2. Add to `.gitignore`
3. Reset and recommit without secrets

### Repository URL
- **HTTPS**: https://github.com/yamb0x/comfyui-cinema4d-bridge.git
- **Web**: https://github.com/yamb0x/comfyui-cinema4d-bridge

---

**Note**: Keep your personal access token secure and never share it publicly.