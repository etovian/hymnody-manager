# Mobile Audio Interruption Resilience & Sanctuary Operation Guide

## 1. Executive Summary

When running **Hymnody Manager** in Sanctuary Mobile Mode on iOS (Safari) or Android (Chrome), incoming notifications (text messages, phone calls, app push alerts) cause the mobile operating system to interrupt playback. This often causes the audio stream to pause indefinitely in the middle of a hymn or liturgical ordinary, requiring manual operator intervention.

This document outlines:
1. The architectural root cause (Mobile OS audio focus and browser sandboxing).
2. Proposed client-side web enhancements to automatically mitigate and recover from interruptions.
3. Operational best practices for church sanctuary audio operators.

---

## 2. Root Cause Analysis

### 2.1 Mobile OS Audio Focus Management
- Both iOS and Android utilize strict audio focus management. When an external sound occurs (such as an SMS notification, incoming call, or timer chime), the operating system grants transient audio focus to the notification.
- To prioritize the notification sound, the OS either ducks (lowers the volume of) background audio or forcibly halts playback on HTML `<audio>` elements.
- On iOS Safari, notification sounds often fire a native `pause` event on the web `<audio>` element without automatically unpausing once the chime finishes.

### 2.2 Web Sandbox Constraints
- Web browsers cannot programmatically manipulate native phone ringers, mute hardware switches, or alter operating system alert settings due to mobile OS security and privacy sandboxes.
- Therefore, software mitigation must focus on **interruption detection**, **automatic recovery**, and **media player elevation**.

---

## 3. Proposed Software Enhancements (Future Session Roadmap)

### 3.1 Transient Interruption Auto-Resume
When an operator starts playback, the application maintains state indicating intended playback (`isPlaying = true`). If the HTML `<audio>` element fires a `pause` event without the operator pressing Pause or the track reaching its natural end, the app can treat the pause as a transient OS interruption.

**Proposed Logic (`src/static/app.js`):**
```javascript
let isUserInitiatedPause = false;

function toggleMobilePlayPause(event) {
  isUserInitiatedPause = true;
  // standard play/pause toggling logic...
}

audioPlayer.addEventListener('pause', () => {
  // If pause fired unexpectedly while the operator expects playback
  if (isPlaying && !isUserInitiatedPause && !audioPlayer.ended) {
    console.warn("Unexpected audio pause detected (possible OS notification interruption). Attempting auto-resume...");
    
    // Allow brief grace period for notification chime to complete (750ms)
    setTimeout(() => {
      if (isPlaying) {
        audioPlayer.play()
          .then(() => {
            console.log("Audio successfully auto-resumed following interruption.");
          })
          .catch((err) => {
            console.warn("Auto-resume prevented by browser policy; user gesture required:", err);
            isPlaying = false;
            updatePlayButtonUI();
          });
      }
    }, 750);
  }
  isUserInitiatedPause = false;
});
```
*Note: Because user gesture permission has already been granted for the active audio session, modern mobile browsers typically permit `.play()` to resume.*

### 3.2 MediaSession API Integration (`navigator.mediaSession`)
Registering playback with the W3C `MediaSession` API marks the audio stream as an active media presentation rather than a transient web page sound effect. This provides:
- Lower likelihood of aggressive OS audio eviction.
- Native lock screen and control center integration (showing hymn title, artist/organist, and playback controls).

**Proposed Implementation:**
```javascript
function updateMediaSession(item) {
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: item.slot_name ? `${item.slot_name}: ${item.display_title}` : item.display_title,
      artist: item.artist || 'The Concordia Organist',
      album: item.album || 'Hymnody Manager',
      artwork: [
        { src: '/static/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
        { src: '/static/icons/icon-512.png', sizes: '512x512', type: 'image/png' }
      ]
    });

    navigator.mediaSession.setActionHandler('play', () => togglePlayPause());
    navigator.mediaSession.setActionHandler('pause', () => togglePlayPause());
    navigator.mediaSession.setActionHandler('previoustrack', () => playPrevTrack());
    navigator.mediaSession.setActionHandler('nexttrack', () => playNextTrack());
  }
}
```

### 3.3 Screen Wake Lock API (`navigator.wakeLock`)
Prevents mobile devices from dimming the screen or entering low-power standby during longer hymns, which can also trigger background audio throttling.

```javascript
let wakeLock = null;

async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch (err) {
    console.debug('Wake lock request ignored:', err);
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release();
    wakeLock = null;
  }
}
```

### 3.4 Sanctuary Operator Tip Banner
Provide a subtle, dismissible tip badge in the Sanctuary Mobile view advising operators on optimal device setup for services.

---

## 4. Operational Best Practices for Sanctuary Operators

Even with auto-resume logic, an audible notification chime from an operator's phone through the church sound system or Bluetooth receiver is disruptive to worship. Sound operators and volunteers should follow these operational protocols:

1. **Enable "Do Not Disturb" (DND) / Worship Focus Mode**:
   - Both iOS and Android support Focus / DND modes that mute all incoming texts, calls, and app badges.
   - Recommended setup: Create a dedicated "Worship" focus profile configured to silence all alerts.
2. **Airplane Mode + Wi-Fi**:
   - Turn on **Airplane Mode**, then turn **Wi-Fi** back on.
   - Cellular text messages (SMS) and incoming cellular phone calls are completely blocked at the carrier level, while the church Wi-Fi network connection to Hymnody Manager continues streaming uninterrupted.
3. **Dedicated Sanctuary Playback Device**:
   - Whenever feasible, utilize a dedicated church tablet or retired smartphone connected permanently to the sound console, with personal communication apps removed and notifications disabled.
