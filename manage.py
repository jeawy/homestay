#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "property.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)

"""
{
    "status": 0,
    "msg": [
        {
            "id": 15,
            "attr_type": 1,
            "attr_name": "排名",
            "attr_value": "1",
            "attr_default": "",
            "entity_id": null,
            "entity_type": 4
        },
        {
            "id": 17,
            "attr_type": 5,
            "attr_name": "优先级",
            "attr_value": "{'selectway': 0, 'selection': {'高': 2, '中': 1, '低': 0}, 'selected':1}",
            "attr_default": "2",
            "entity_id": null,
            "entity_type": 4
        }
    ]
}
"""