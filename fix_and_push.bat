@echo off
git add .
git commit -m "FIX: Personal cabinet database and import errors

- Fixed migration 016 to create users table if not exists
- Fixed import errors: spend_points -> subtract_karma, add_points -> add_karma
- Added get_or_create_user function
- Fixed function parameter names: description -> reason
- Personal cabinet should now work without errors"
git push origin main
