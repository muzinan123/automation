# -*- coding:utf8 -*-

from difflib import unified_diff


class DiffService(object):

    @staticmethod
    def diff(origin=None, new=None):
        if origin:
            origin = [e + "\n" for e in origin.split("\n")]
        else:
            origin = []
        new = [e + "\n" for e in new.split("\n")]
        diff = list()
        for line in unified_diff(origin, new, fromfile="a/origin", tofile="b/new", n=65535):
            diff.append(line)
        if not diff:
            diff.append("--- a/origin\n")
            diff.append("+++ b/new\n")
            diff.append("@@ -0,0 +0,0 @@\n")
            diff.extend([" " + e for e in origin])
        diff.insert(0, "diff --text a/origin b/new\n")
        diff.insert(1, "index 0a534ec..0b7b2f0 100644\n")
        return ''.join(diff)

    @staticmethod
    def compare_list(origin=list(), new=list()):
        origin_dict = {e.get('k'): e.get('v') for e in origin}
        new_dict = {e.get('k'): e.get('v') for e in new}
        all_key = set([e.get('k') for e in origin]) | set([e.get('k') for e in new])
        ret = list()
        for k in all_key:
            ret.append({'k': k, 'ov': origin_dict.get(k), 'nv': new_dict.get(k)})
        ret.sort(key=lambda x: x.get('k'))
        return ret
