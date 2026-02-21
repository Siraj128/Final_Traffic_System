"""
profile_manager.py

Manages the pool of 100 Dummy Profiles for the Global Demo Mode.
- Loads profiles from config/dummy_profiles.json
- Assigns profiles to vehicle Track IDs
- Recycles profiles when vehicles leave the frame

Author: Auto-Generated
"""

import json
import os
import random
import threading

class ProfileManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ProfileManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.profiles = []
        self.available_indices = set()
        self.used_indices = set() # Maps TrackID -> ProfileIndex? No, just set of indices
        self.lock = threading.Lock()
        
        self._load_profiles()

    def _load_profiles(self):
        """Load 100 users and flatten into 200 unique plate profiles."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "..", "..", "config", "dummy_profiles_100.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    users = json.load(f)
                
                self.profiles = []
                for u in users:
                    # Vehicle 1
                    self.profiles.append({
                        "plate": u["v1_plate"],
                        "owner": u["owner"],
                        "phone": u["phone"],
                        "score": u["score"]
                    })
                    # Vehicle 2
                    self.profiles.append({
                        "plate": u["v2_plate"],
                        "owner": u["owner"],
                        "phone": u["phone"],
                        "score": u["score"]
                    })
                
                self.available_indices = set(range(len(self.profiles)))
                print(f"  >> [ProfileManager] Flattened {len(users)} users into {len(self.profiles)} active plates.")
            else:
                print(f"  !! [ProfileManager] Config not found: {config_path}")
                self.profiles = [{"plate": f"MH12-DE-{1000+i}", "owner": "Demo User", "phone": f"9000000{i:03d}"} for i in range(200)]
                self.available_indices = set(range(200))
                
        except Exception as e:
            print(f"  XX [ProfileManager] Load Error: {e}")

    def get_profile(self):
        """
        Checkout a random available profile.
        Returns: dict (Profile) or None if pool empty.
        """
        with self.lock:
            if not self.available_indices:
                # Reuse used ones if we run out? Or just return None?
                # For demo safety, let's recycle random used one if strictly needed, 
                # but with 100 profiles and ~10 cars per frame, we should be fine.
                return None
            
            idx = random.choice(list(self.available_indices))
            self.available_indices.remove(idx)
            self.used_indices.add(idx)
            
            # Return a COPY to prevent modification
            profile = self.profiles[idx].copy()
            profile["_index"] = idx # Internal tracking
            return profile

    def release_profile(self, profile):
        """
        Return a profile to the pool.
        Args:
            profile (dict): The profile object returned by get_profile()
        """
        if not profile or "_index" not in profile:
            return

        idx = profile["_index"]
        with self.lock:
            if idx in self.used_indices:
                self.used_indices.remove(idx)
                self.available_indices.add(idx)
                # print(f"  ♻️ [ProfileManager] Recycled Profile: {profile.get('plate')}")
