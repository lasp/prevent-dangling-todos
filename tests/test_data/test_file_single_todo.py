"""Test file for testing comment prefix filtering."""


# TODO: This TODO has no reference
def todo_function():
    pass


# TODO MYJIRA-100: This TODO is properly referenced
def proper_todo():
    return True


# FIXME MYJIRA-200: This FIXME is properly referenced
def fixme_function():
    # Not a TODO or work comment, just regular comment
    pass


# HACK MYJIRA-300: This HACK is properly referenced
class TestClass:
    # BUG MYJIRA-400: Bug with reference
    def method(self):
        # Regular comment without keywords
        return None


# More TODOs for testing
# TODO: Another dangling TODO
# TODO : TODO with extra spacing


def regular_function():
    # This function has no work comments
    # Just regular comments explaining code
    x = 1
    y = 2
    return x + y
