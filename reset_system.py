import os

FILES_TO_RESET = [
    "slots_db.json",
    "booking_queue.db",
    "notifications_db.json"
]

def reset():
    print("🧹 Cleaning up system state...")
    for filename in FILES_TO_RESET:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"✅ Deleted {filename}")
            except Exception as e:
                print(f"❌ Failed to delete {filename}: {e}")
        else:
            print(f"ℹ️  {filename} not found (already clean)")

    print("\n✨ System Reset Complete. Restart your agents now.")

if __name__ == "__main__":
    reset()
