"""Regression checks for reference metadata and example generation.

Run with Harnest's development Python: python scripts/test_harnest_reference.py.
"""
import ast
from pathlib import Path
import runpy
import tempfile
from typing import Annotated, Callable
import unittest

from pydantic import BaseModel, Field


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.api = runpy.run_path(str(Path(__file__).with_name('generate-harnest-reference.py')))

    def test_description_precedence(self):
        """Curated details override docs, fields, interface contracts, and shared text."""
        api = self.api
        class Contract:
            __module__ = 'harnest.example'
            def fetch(self, item):
                pass
        class Store(Contract):
            def fetch(self, item):
                """Read a record.

                Args:
                    item: from docstring
                """
        api['SHARED']['params']['item'] = 'shared'
        api['INTERFACES'].append((Contract, 'harnest.example'))
        api['ALL_DETAILS']['harnest.example'] = {'Contract.fetch': {'params': {'item': 'interface'}}}
        api['PAGE_DETAILS'].update({'*.fetch': {'params': {'item': 'wildcard'}},
                                   'Store.fetch': {'params': {'item': 'curated'}}})
        def description():
            return api['details_for']('Store.fetch', Store.fetch, {'item': 'field'}, Store)[0]['item']
        self.assertEqual(description(), 'curated')
        api['PAGE_DETAILS'].pop('Store.fetch')
        self.assertEqual(description(), 'wildcard')
        api['PAGE_DETAILS'].clear()
        self.assertEqual(description(), 'from docstring')
        Store.fetch.__doc__ = None
        self.assertEqual(description(), 'field')
        self.assertEqual(api['details_for']('Store.fetch', Store.fetch, owner=Store)[0]['item'], 'interface')
        api['INTERFACES'].clear()
        self.assertEqual(api['details_for']('Store.fetch', Store.fetch, owner=Store)[0]['item'], 'shared')

    def test_stale_metadata_fails(self):
        """Unmatched shared keys, members, and wildcard parameters cannot disappear silently."""
        api = self.api
        def fetch(item):
            pass
        api['SHARED']['params']['removed'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'match no rendered parameter'):
            api['validate_shared']()
        api['PAGE_DETAILS']['*.removed'] = {'params': {'item': 'stale'}}
        with self.assertRaisesRegex(ValueError, 'matches no rendered member'):
            api['validate_details']('harnest.example')
        api['PAGE_DETAILS'].clear()
        api['PAGE_DETAILS']['*.fetch'] = {'params': {'typo': 'stale'}}
        api['details_for']('Store.fetch', fetch)
        with self.assertRaisesRegex(ValueError, 'unknown parameters'):
            api['validate_details']('harnest.example')

    def test_yaml_duplicates_and_shared_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'details.yaml'
            path.write_text('one: &params\n  item: description\ntwo: *params\n')
            data = self.api['read_yaml'](path)
            self.assertEqual(data['one'], data['two'])
            path.write_text('one:\n  item: first\n  item: second\n')
            with self.assertRaisesRegex(ValueError, 'duplicate keys'):
                self.api['read_yaml'](path)

    def test_field_aliases_and_annotation_display(self):
        class Config(BaseModel):
            path: Annotated[str, Field(alias='location', description='Storage location')]
        docs = self.api['class_field_docs'](Config, 'Config')
        self.assertEqual(docs['location'], 'Storage location')
        table = '\n'.join(self.api['parameter_table'](Config, docs))
        self.assertIn('`location` | `str`', table)
        self.assertNotIn('Annotated', table)

    def test_examples_distinguish_factory_decorator_and_callable(self):
        class Client:
            @classmethod
            def connect(cls, endpoint: str) -> 'Client':
                return cls()
        example = '\n'.join(self.api['class_example'](Client, 'harnest.example', 'Client', False))
        self.assertIn('Client.connect(endpoint=...)', example)
        def wrap_call(value) -> Callable[..., object]:
            pass
        def decorator(function: Callable) -> Callable:
            pass
        def bind_arguments(function: Callable, args: tuple, kwargs: dict) -> dict:
            return kwargs
        self.assertFalse(self.api['is_decorator'](bind_arguments))
        self.assertFalse(self.api['is_decorator'](wrap_call))
        self.assertTrue(self.api['is_decorator'](decorator))
        code = 'result = function(' + ', '.join(f'argument_{i}=...' for i in range(12)) + ')'
        wrapped = self.api['wrap'](code)
        self.assertEqual(ast.dump(ast.parse(code)), ast.dump(ast.parse(wrapped)))
        self.assertLessEqual(len(wrapped.splitlines()), 7)


if __name__ == '__main__':
    unittest.main()
