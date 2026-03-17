# CineTrack Pro - Troubleshooting Guide

## Common Issues and Solutions

### Issue: Camera moves when add-on is installed but not in use
**Cause:** Frame handler was running even when features disabled
**Solution:** 
- This was fixed in v2.1.0
- Update to latest version
- Verify Tracking/Shake are disabled until ready

### Issue: Camera not following target
**Checklist:**
1. Is tracking enabled? (Main panel)
2. Is target object selected? (Tracking panel)
3. Is the camera selected in "Target Camera"?
4. Are you in an active viewport?
5. Try baking the tracking to verify

**Quick Fix:**
```python
# Reset and re-enable
1. Disable Tracking
2. Re-select target object
3. Re-enable Tracking