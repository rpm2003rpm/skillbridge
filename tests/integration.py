from time import sleep
from warnings import warn
from pytest import fixture, mark, raises, skip
import unittest
import sys
sys.path.insert(0, "../")
from skillbridge import RemoteObject, RemoteTable, SkillCode, Symbol, Unbound, Workspace

class TestSkillbridge(unittest.TestCase):

    def test_can_add_two_numbers(self):
        ws = Workspace()
        self.assertEqual(ws.functions.plus(2,3), 5)
        self.assertEqual(ws.runSkillCode('plus(2 53)'), 55)
        ws.close()

    def test_can_create_a_hash_table(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', Unbound)
        self.assertEqual(isinstance(t, RemoteTable), True)
        ws.close()

    def test_can_store_keys_in_hash_table(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', Unbound)
        t['x'] = 123
        t[123] = [2, 3, 4]
        self.assertEqual(t['x'], 123)
        self.assertEqual(t[123], [2, 3, 4])
        ws.close()

    def test_can_iterate_over_hash_table_keys(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', Unbound)
        self.assertEqual(list(t), [])
        t['x'] = 1
        self.assertEqual(list(t), ['x'])
        t[2] = 3
        self.assertEqual(list(t), ['x', 2])
        ws.close()

    def test_can_use_hash_table_like_a_dict(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', Unbound)
        self.assertEqual(dict(t), {})
        t['x'] = 1
        self.assertEqual(dict(t), {'x':1})
        t.update(y=3)
        self.assertEqual(dict(t), {'x':1, 'y':3})
        ws.close()

    def test_can_use_symbol_keys_in_hash_table(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', None)
        t[Symbol('key')] = 123
        self.assertEqual(t['key'], None)
        self.assertEqual(t[Symbol('key')], 123)
        ws.close()

    def test_missing_key_raises_key_error(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', Unbound)
        with raises(KeyError, match=r'XYZ'):
            _ = t['XYZ']
        ws.close()

    def test_open_file(self):
        ws = Workspace()
        fun = ws.functions
        file = fun.outfile('__test_skill_python.txt', 'w')
        self.assertEqual(file._is_open_file(), True)
        self.assertEqual(str(file).startswith('<remote __py_openfile'), True)
        self.assertEqual(isinstance(dir(file), list), True)
        ws.close()

    def test_remote_object(self):
        ws = Workspace()
        fun = ws.functions
        libs = fun.ddGetLibList()
        assert libs
        lib = libs[0]
        self.assertEqual(str(lib).startswith('<remote __py_dd_'), True)
        self.assertEqual(set(dir(lib)) > {'cells', 'isReadable', 'group', 'name'}, True)
        self.assertEqual(lib.isReadable,lib['isReadable'])
        with raises(AttributeError):
            _ = lib._repr_html_
        lib.getdoc()
        self.assertEqual(lib, lib)  # noqa: PLR0124
        self.assertNotEqual(lib, libs[1])
        self.assertNotEqual(lib, 1)  
        self.assertNotEqual(lib, 1)
        ws.close()

    def test_pointer(self):
        ws = Workspace()
        fun = ws.functions
        lib = max(fun.ddGetLibList(), key=lambda lib: len(lib.cells or ()))
        cells = lib.pattr('cells')
        self.assertEqual(isinstance(lib.cells, list), True)
        self.assertEqual(isinstance(cells, RemoteObject), True)
        self.assertEqual(cells[0], lib.cells[0])
        ws.close()

    def test_vector_without_default(self):
        ws = Workspace()
        fun = ws.functions
        v = fun.makeVector(10)
        self.assertEqual(len(v), 10)
        for i in range(-7, 14):
            with raises(IndexError, match=str(i)):
                _ = v[i]
        v[0] = 10
        v[2] = 12
        self.assertEqual(list(v), [10])
        v[1] = 11
        self.assertEqual(list(v), [10, 11, 12])
        self.assertEqual(v[0], 10)
        with raises(IndexError, match='10'):
            v[10] = 100
        ws.close()

    def test_direct_globals(self):
        ws = Workspace()
        ws.__.myGlobalValue = 102030
        self.assertEqual(ws.__.myGlobalValue, 102030)
        self.assertEqual(ws.__['myGlobalValue'], 102030)
        ws.close()

    def test_collections_with_default(self):
        ws = Workspace()
        fun = ws.functions
        t = fun.makeTable('T', 123)
        self.assertEqual(t[10], 123)
        v = fun.makeVector(10, 12)
        self.assertEqual(list(v), [12] * 10)
        ws.close()

    def test_outstring(self):
        ws = Workspace()
        fun = ws.functions
        outstring = fun.outstring
        get_outstring = fun.getOutstring
        close = fun.close
        fprintf = fun.fprintf
        s = outstring()
        self.assertEqual(get_outstring(s), "")  # noqa: PLC1901
        self.assertEqual(fprintf(s, "Hello "), True)
        self.assertEqual(get_outstring(s), "Hello ")
        self.assertEqual(fprintf(s, "World"), True)
        self.assertEqual(get_outstring(s), "Hello World")
        self.assertEqual(close(s), True)
        self.assertEqual(get_outstring(s), None)
        ws.close()

    def test_nil_t_nil_is_not_a_disembodied_property_list(self):
        ws = Workspace()
        fun = ws.functions  
        self.assertEqual(fun.cdr([0, None, True, None]), [None, True, None])
        ws.close()

    #def test_table_getattr_is_equivalent_to_symbol_lookup(self):
    #    ws = Workspace()
    #    fun = ws.functions
    #    t = fun.makeTable('T', Unbound)
    #    t[Symbol('abcDef')] = 10
    #    self.assertEqual(t.abcDef, 10)
        #t.xyz_abc = 20
        #self.assertEqual(t[Symbol('xyzAbc')], 20)
    #    ws.close()

if __name__ == '__main__':
    unittest.main()
