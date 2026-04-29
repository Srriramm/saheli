import 'package:geolocator/geolocator.dart';

class LatLng {
  final double latitude;
  final double longitude;
  const LatLng(this.latitude, this.longitude);
}

/// Best-effort GPS lookup. Returns null if location services are off, the
/// user denies the permission, or the fix takes too long. Triage continues
/// regardless — the backend falls back to a default district coordinate
/// when lat/lng are absent, so the demo never blocks on GPS.
Future<LatLng?> getCurrentLocation() async {
  try {
    if (!await Geolocator.isLocationServiceEnabled()) return null;

    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
    }
    if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) {
      return null;
    }

    final pos = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: Duration(seconds: 8),
      ),
    );
    return LatLng(pos.latitude, pos.longitude);
  } catch (_) {
    return null;
  }
}
