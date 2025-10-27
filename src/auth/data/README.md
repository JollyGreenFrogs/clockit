# Common Passwords Data Directory

This directory contains the list of common/weak passwords that are blocked during user registration.

## Files

- `common_passwords.txt` - List of passwords to block (one per line)

## Maintenance

### Updating the Password List

Use the provided script to update the password list:

```bash
./scripts/update-password-list.sh
```

This script provides options to:
1. Keep the current list
2. Download an updated list from SecLists (recommended quarterly)
3. Add custom passwords to the existing list

### Manual Update

You can manually edit `common_passwords.txt`:
- One password per line
- Lines starting with `#` are comments and ignored
- Empty lines are ignored
- Passwords are checked case-insensitively

Example:
```
# Custom company passwords to block
CompanyName123
CompanyName2025
internal123
```

### Recommended Sources

For comprehensive password lists, refer to:
- [SecLists](https://github.com/danielmiessler/SecLists) - Comprehensive security testing lists
- [HaveIBeenPwned](https://haveibeenpwned.com/Passwords) - Pwned Passwords database
- [NCSC Password Guidance](https://www.ncsc.gov.uk/collection/passwords) - UK National Cyber Security Centre

### Performance Considerations

The password list is:
- Loaded once at application startup
- Cached in memory for fast lookups
- Currently contains ~150+ passwords
- Can be expanded to thousands without performance impact

For extremely large lists (100K+), consider:
- Using a hash-based lookup (e.g., bloom filter)
- Splitting into tiers (most common checked first)
- External API like HaveIBeenPwned Passwords API

### Security Best Practices

1. **Regular Updates**: Update the list quarterly or when major breaches occur
2. **Balance Security vs UX**: Very large lists may frustrate users
3. **Custom Additions**: Add company-specific or industry-specific weak passwords
4. **Monitor Trends**: Stay updated on password trends and attacks

### Testing

After updating the list, test that common passwords are properly blocked:

```bash
# Set test environment
export ENVIRONMENT=test
export DEV_MODE=sqlite
export SECRET_KEY="test-secret-key-for-ci-testing-at-least-32-characters-long"

# Run password validation tests
pytest tests/test_auth.py::TestUserRegistration::test_register_weak_password -v
```

## Implementation Details

The password validation (`src/auth/services.py`):
1. Loads the password list at first validation
2. Caches the list in memory as a set for O(1) lookups
3. Compares passwords case-insensitively
4. Falls back to a minimal hardcoded list if file is missing

This approach provides:
- ✅ Fast validation (sub-millisecond)
- ✅ Easy maintenance (edit text file)
- ✅ No external dependencies
- ✅ Graceful degradation if file is missing
