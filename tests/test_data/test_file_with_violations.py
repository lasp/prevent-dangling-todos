# Test file with various TODO patterns

# TODO: This is a violation - no Jira reference
def function1():
    pass


# FIXME: Another violation without ticket
def function2():
    # TODO MYJIRA-123: This one is properly referenced
    return True


# XXX: Missing Jira reference here
class TestClass:
    # HACK MYJIRA-456: Properly referenced hack
    def method(self):
        # BUG: This bug has no ticket
        pass


# REVIEW: Need to review this code
# OPTIMIZE: Performance could be better
# REFACTOR: This needs refactoring

# Properly formatted comments:
# TODO MYJIRA-789: Complete implementation
# FIXME MYJIRA-101: Handle edge cases
