#!/usr/bin/env python3
"""
Python Simpler - Full Production Runtime System
Real-time translation dengan caching, multi-file support, dan error handling
"""

import ast
import os
import sys
import types
import time
import hashlib
import importlib.util
from typing import Dict, List, Any, Optional
from collections import defaultdict
import traceback
import re

class MemoryAwareCache:
    """LRU Cache dengan memory management"""
    def __init__(self, max_size: int = 10000):
        self.cache = {}
        self.access_count = defaultdict(int)
        self.access_time = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.access_count[key] += 1
            self.access_time[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            # LRU eviction - remove oldest accessed
            oldest_key = min(self.access_time, key=self.access_time.get)
            del self.cache[oldest_key]
            del self.access_count[oldest_key]
            del self.access_time[oldest_key]
        
        self.cache[key] = value
        self.access_count[key] = 1
        self.access_time[key] = time.time()
    
    def clear(self):
        self.cache.clear()
        self.access_count.clear()
        self.access_time.clear()

class IndonesianTransformer(ast.NodeTransformer):
    """AST Transformer untuk handle complex expressions"""
    
    def __init__(self, function_map: Dict[str, str]):
        self.function_map = function_map
        self.required_imports = set()
    
    def visit_Call(self, node):
        """Transform function calls"""
        if isinstance(node.func, ast.Name):
            original_name = node.func.id
            if original_name in self.function_map:
                new_name = self.function_map[original_name]
                
                # Handle imports yang dibutuhkan
                if '.' in new_name:
                    module_name = new_name.split('.')[0]
                    self.required_imports.add(f"import {module_name}")
                
                node.func.id = new_name
        
        return self.generic_visit(node)
    
    def visit_Name(self, node):
        """Transform variable names dan constants"""
        if node.id in self.function_map:
            node.id = self.function_map[node.id]
        return node

class SmartTranslator:
    """Core translation engine dengan multiple strategies"""
    
    def __init__(self):
        self.function_map = self._build_function_map()
        self.cache = MemoryAwareCache(max_size=5000)
        self.ast_cache = MemoryAwareCache(max_size=1000)
        self.line_cache = MemoryAwareCache(max_size=10000)
        
        # Performance tracking
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'translations': 0,
            'ast_transformations': 0
        }
    
    def _build_function_map(self) -> Dict[str, str]:
        """Build comprehensive function mapping"""
        return {
            # Basic I/O - Multiple aliases dengan prioritas
            'cetak': 'print', 'tampilkan': 'print', 'tulis': 'print', 'keluarkan': 'print',
            'masukan': 'input', 'input_pengguna': 'input', 'ambil_input': 'input', 'tanya': 'input',
            
            # Data Type Conversion
            'ke_angka': 'int', 'ke_integer': 'int', 'ke_bilangan': 'int',
            'ke_desimal': 'float', 'ke_float': 'float', 'ke_pecahan': 'float',
            'ke_teks': 'str', 'ke_string': 'str', 'ke_kata': 'str',
            'ke_boolean': 'bool', 'ke_bool': 'bool',
            
            # String Operations
            'panjang': 'len', 'ukuran': 'len', 'hitung': 'len', 'banyak': 'len',
            'gabung': 'join', 'sambung': 'join', 'satukan': 'join',
            'pisah': 'split', 'bagi': 'split', 'potong': 'split', 'pecah': 'split',
            'ganti': 'replace', 'ubah': 'replace', 'tukar': 'replace', 'substitusi': 'replace',
            'cari': 'find', 'temukan': 'find', 'lokasi': 'find', 'posisi': 'find',
            'huruf_besar': 'upper', 'kapital': 'upper', 'besar_semua': 'upper',
            'huruf_kecil': 'lower', 'kecil_semua': 'lower', 'lowercase': 'lower',
            'awalan': 'startswith', 'dimulai_dengan': 'startswith',
            'akhiran': 'endswith', 'diakhiri_dengan': 'endswith',
            'hapus_spasi': 'strip', 'trim': 'strip', 'bersihkan': 'strip',
            
            # List Operations
            'daftar': 'list', 'buat_daftar': 'list', 'array': 'list', 'senarai': 'list',
            'tambah': 'append', 'masukkan': 'append', 'sisipkan': 'insert',
            'hapus': 'remove', 'buang': 'remove', 'hilangkan': 'pop', 'keluarkan': 'pop',
            'urutkan': 'sort', 'sortir': 'sort', 'susun': 'sort', 'atur': 'sorted',
            'balik': 'reverse', 'kebalikan': 'reverse', 'terbalik': 'reversed',
            'salin': 'copy', 'duplikat': 'copy', 'kopi': 'copy',
            'kosongkan': 'clear', 'bersihkan_daftar': 'clear',
            'hitung_item': 'count', 'jumlah_item': 'count',
            
            # Dictionary Operations
            'kamus': 'dict', 'dictionary': 'dict', 'buat_kamus': 'dict', 'peta': 'dict',
            'kunci': 'keys', 'semua_kunci': 'keys', 'daftar_kunci': 'keys',
            'nilai': 'values', 'semua_nilai': 'values', 'daftar_nilai': 'values',
            'item': 'items', 'semua_item': 'items', 'pasangan': 'items',
            'ambil': 'get', 'dapatkan': 'get', 'cari_nilai': 'get',
            'perbarui': 'update', 'gabung_kamus': 'update',
            
            # File Operations
            'buka_file': 'open', 'baca_file': 'open', 'akses_file': 'open',
            'tutup_file': 'close', 'simpan_file': 'write',
            
            # Math Operations
            'maksimum': 'max', 'terbesar': 'max', 'paling_besar': 'max',
            'minimum': 'min', 'terkecil': 'min', 'paling_kecil': 'min',
            'jumlah': 'sum', 'total': 'sum', 'tambah_semua': 'sum', 'sigma': 'sum',
            'rata_rata': 'statistics.mean', 'mean': 'statistics.mean', 'rerata': 'statistics.mean',
            'median': 'statistics.median', 'nilai_tengah': 'statistics.median',
            'bulat': 'round', 'pembulatan': 'round', 'bulatkan': 'round',
            'absolut': 'abs', 'mutlak': 'abs', 'nilai_absolut': 'abs',
            'pangkat': 'pow', 'eksponen': 'pow', 'kuadrat': 'pow',
            
            # Range and Iteration
            'rentang': 'range', 'jangkauan': 'range', 'dari_sampai': 'range',
            'enumerasi': 'enumerate', 'enum': 'enumerate', 'nomori': 'enumerate',
            'zip_data': 'zip', 'gabung_data': 'zip', 'pasangkan': 'zip',
            
            # Type Checking
            'tipe': 'type', 'jenis': 'type', 'type_data': 'type',
            'adalah_angka': 'isinstance', 'adalah_teks': 'isinstance',
            
            # Control Flow Keywords
            'jika': 'if', 'kalau': 'if', 'bila': 'if', 'andai': 'if',
            'atau_jika': 'elif', 'atau_kalau': 'elif', 'else_if': 'elif',
            'selain_itu': 'else', 'lainnya': 'else', 'jika_tidak': 'else',
            'untuk': 'for', 'setiap': 'for', 'tiap': 'for',
            'selama': 'while', 'ketika': 'while', 'saat': 'while',
            'dalam': 'in', 'di': 'in', 'pada': 'in', 'ada_dalam': 'in',
            'keluar': 'break', 'berhenti': 'break', 'stop': 'break',
            'lanjut': 'continue', 'skip': 'continue', 'lewati': 'continue',
            'kembali': 'return', 'kembalikan': 'return', 'hasil': 'return',
            
            # Boolean and Logic
            'benar': 'True', 'ya': 'True', 'iya': 'True',
            'salah': 'False', 'tidak': 'False', 'bukan': 'False',
            'kosong': 'None', 'tidak_ada': 'None', 'null': 'None',
            'dan': 'and', 'serta': 'and', 'juga': 'and',
            'atau': 'or', 'ataupun': 'or',
            'bukan': 'not', 'tidak': 'not', 'negate': 'not',
            
            # Exception Handling
            'coba': 'try', 'percobaan': 'try',
            'kecuali': 'except', 'tangkap': 'except', 'error': 'except',
            'akhirnya': 'finally', 'terakhir': 'finally',
            'lempar': 'raise', 'angkat': 'raise', 'throw': 'raise',
            
            # Class and Object
            'kelas': 'class', 'class': 'class', 'objek': 'object',
            'diri': 'self', 'ini': 'self',
            'super_class': 'super', 'induk': 'super',
            
            # Import and Module
            'impor': 'import', 'muat': 'import', 'gunakan': 'import',
            'dari': 'from', 'ambil_dari': 'from',
            'sebagai': 'as', 'alias': 'as', 'dengan_nama': 'as',
            
            # Advanced
            'lambda_func': 'lambda', 'fungsi_anonim': 'lambda',
            'generator': 'yield', 'hasilkan': 'yield',
            'dengan': 'with', 'gunakan_dengan': 'with',
            'tegas': 'assert', 'pastikan': 'assert', 'validasi': 'assert',
            
            # Database (common patterns)
            'buka_database': 'sqlite3.connect',
            'eksekusi_sql': 'execute',
            'ambil_data': 'fetchall',
            'ambil_satu': 'fetchone',
            'commit_db': 'commit',
            'tutup_db': 'close',
        }
    
    def _create_line_hash(self, line: str) -> str:
        """Create hash for caching"""
        return hashlib.md5(line.encode()).hexdigest()
    
    def _simple_translation(self, line: str) -> str:
        """Fast string-based translation for simple cases"""
        translated = line
        
        # Sort by length descending untuk avoid partial replacement
        sorted_functions = sorted(self.function_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for indo_word, python_word in sorted_functions:
            # Word boundary pattern untuk precision
            pattern = r'\b' + re.escape(indo_word) + r'\b'
            translated = re.sub(pattern, python_word, translated)
        
        return translated
    
    def _ast_translation(self, code: str) -> tuple[str, set]:
        """AST-based translation for complex expressions"""
        try:
            tree = ast.parse(code)
            transformer = IndonesianTransformer(self.function_map)
            new_tree = transformer.visit(tree)
            
            # Fix missing locations
            ast.fix_missing_locations(new_tree)
            
            translated_code = ast.unparse(new_tree)
            return translated_code, transformer.required_imports
            
        except SyntaxError:
            # Fallback to simple translation
            return self._simple_translation(code), set()
    
    def translate_line(self, line: str) -> str:
        """Translate single line dengan caching"""
        if not line.strip() or line.strip().startswith('#'):
            return line
        
        line_hash = self._create_line_hash(line)
        cached = self.line_cache.get(line_hash)
        
        if cached:
            self.stats['cache_hits'] += 1
            return cached
        
        self.stats['cache_misses'] += 1
        self.stats['translations'] += 1
        
        # Detect complexity untuk pilih strategy
        is_complex = any(char in line for char in ['(', ')', '[', ']', '.'])
        
        if is_complex and len(line.strip()) > 20:
            # Use AST for complex expressions
            try:
                translated, imports = self._ast_translation(line)
                self.stats['ast_transformations'] += 1
            except:
                translated = self._simple_translation(line)
        else:
            # Use simple translation for basic cases
            translated = self._simple_translation(line)
        
        self.line_cache.set(line_hash, translated)
        return translated
    
    def translate_code(self, code: str) -> tuple[str, set]:
        """Translate entire code block"""
        lines = code.split('\n')
        translated_lines = []
        all_imports = set()
        
        for line in lines:
            translated_line = self.translate_line(line)
            translated_lines.append(translated_line)
        
        # Try AST translation for the whole block untuk better import detection
        try:
            full_translated = '\n'.join(translated_lines)
            ast_translated, imports = self._ast_translation(full_translated)
            all_imports.update(imports)
            return ast_translated, all_imports
        except:
            return '\n'.join(translated_lines), all_imports
    
    def get_stats(self) -> dict:
        """Get performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.line_cache.cache)
        }

class VirtualModuleLoader:
    """Load dan translate Indonesian Python modules"""
    
    def __init__(self, translator: SmartTranslator):
        self.translator = translator
        self.loaded_modules = {}
        self.module_cache = MemoryAwareCache(max_size=100)
    
    def load_module(self, module_path: str) -> types.ModuleType:
        """Load dan translate module"""
        if module_path in self.loaded_modules:
            return self.loaded_modules[module_path]
        
        # Check cache
        cached_module = self.module_cache.get(module_path)
        if cached_module:
            self.loaded_modules[module_path] = cached_module
            return cached_module
        
        # Read original file
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                indo_code = f.read()
        except FileNotFoundError:
            raise ImportError(f"Cannot find module: {module_path}")
        
        # Translate module
        python_code, imports = self.translator.translate_code(indo_code)
        
        # Add required imports
        if imports:
            import_lines = '\n'.join(sorted(imports)) + '\n\n'
            python_code = import_lines + python_code
        
        # Create virtual module
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        module = types.ModuleType(module_name)
        module.__file__ = module_path
        
        # Execute translated code in module namespace
        try:
            exec(python_code, module.__dict__)
        except Exception as e:
            raise ImportError(f"Error executing module {module_path}: {e}")
        
        # Cache dan store
        self.module_cache.set(module_path, module)
        self.loaded_modules[module_path] = module
        
        return module

class PythonSimplerRuntime:
    """Main runtime environment untuk Python Simpler"""
    
    def __init__(self, debug: bool = False):
        self.translator = SmartTranslator()
        self.module_loader = VirtualModuleLoader(self.translator)
        self.debug = debug
        self.execution_globals = {}
        self.execution_locals = {}
        
        # Setup built-in functions
        self._setup_builtins()
    
    def _setup_builtins(self):
        """Setup built-in functions untuk environment"""
        # Handle __builtins__ yang bisa berupa module atau dict
        if isinstance(__builtins__, dict):
            self.execution_globals.update(__builtins__)
        else:
            # __builtins__ adalah module
            self.execution_globals.update(__builtins__.__dict__)
        
        # Add custom Indonesian functions dengan error handling
        modules_to_import = {
            'statistik': 'statistics',
            'sqlite3': 'sqlite3', 
            'os': 'os',
            'sys': 'sys',
            'time': 'time',
            'math': 'math',
            'random': 'random',
            'json': 'json',
            're': 're',
        }
        
        for alias, module_name in modules_to_import.items():
            try:
                self.execution_globals[alias] = __import__(module_name)
            except ImportError:
                if self.debug:
                    print(f"Warning: Could not import {module_name}")
                pass
    
    def execute_line(self, line: str) -> Any:
        """Execute single line"""
        if not line.strip():
            return None
        
        translated = self.translator.translate_line(line)
        
        if self.debug:
            print(f"Original: {line}")
            print(f"Translated: {translated}")
        
        try:
            # Use eval for expressions, exec for statements
            if self._is_expression(translated):
                result = eval(translated, self.execution_globals, self.execution_locals)
                return result
            else:
                exec(translated, self.execution_globals, self.execution_locals)
                return None
        except Exception as e:
            # Pass through original Python errors
            raise e
    
    def execute_code(self, code: str) -> Any:
        """Execute code block"""
        translated_code, imports = self.translator.translate_code(code)
        
        # Add required imports
        if imports:
            for imp in imports:
                exec(imp, self.execution_globals)
        
        if self.debug:
            print("="*50)
            print("ORIGINAL CODE:")
            print(code)
            print("\nTRANSLATED CODE:")
            print(translated_code)
            print("="*50)
        
        try:
            exec(translated_code, self.execution_globals, self.execution_locals)
        except Exception as e:
            if self.debug:
                traceback.print_exc()
            raise e
    
    def execute_file(self, filepath: str):
        """Execute Indonesian Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Set __file__ untuk proper imports
            self.execution_globals['__file__'] = os.path.abspath(filepath)
            self.execution_globals['__name__'] = '__main__'
            
            self.execute_code(code)
            
        except Exception as e:
            print(f"Error executing {filepath}: {e}")
            if self.debug:
                traceback.print_exc()
    
    def _is_expression(self, code: str) -> bool:
        """Check if code is expression or statement"""
        try:
            ast.parse(code, mode='eval')
            return True
        except SyntaxError:
            return False
    
    def interactive_mode(self):
        """Start interactive REPL"""
        print("🚀 Python Simpler Interactive Mode")
        print("Ketik 'keluar()' atau Ctrl+C untuk exit")
        print("Ketik 'stats()' untuk melihat performance stats")
        print("-" * 50)
        
        while True:
            try:
                line = input(">>> ")
                
                if line.strip() in ['keluar()', 'exit()', 'quit()']:
                    break
                elif line.strip() == 'stats()':
                    stats = self.translator.get_stats()
                    for key, value in stats.items():
                        print(f"{key}: {value}")
                    continue
                elif line.strip() == 'clear_cache()':
                    self.translator.cache.clear()
                    self.translator.line_cache.clear()
                    print("Cache cleared!")
                    continue
                
                result = self.execute_line(line)
                if result is not None:
                    print(result)
                    
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def run_project(self, project_dir: str):
        """Run entire project dengan multi-file support"""
        main_file = None
        
        # Look for main file
        possible_mains = ['main.py', 'app.py', 'run.py', '__main__.py']
        for main in possible_mains:
            main_path = os.path.join(project_dir, main)
            if os.path.exists(main_path):
                main_file = main_path
                break
        
        if not main_file:
            print(f"No main file found in {project_dir}")
            return
        
        # Change to project directory
        old_cwd = os.getcwd()
        os.chdir(project_dir)
        
        try:
            # Add project dir to path
            sys.path.insert(0, project_dir)
            self.execute_file(main_file)
        finally:
            os.chdir(old_cwd)
            if project_dir in sys.path:
                sys.path.remove(project_dir)

def main():
    """Main entry point"""
    runtime = PythonSimplerRuntime(debug=True)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'interactive':
            runtime.interactive_mode()
        elif sys.argv[1] == 'project':
            if len(sys.argv) > 2:
                runtime.run_project(sys.argv[2])
            else:
                print("Usage: python main.py project <project_directory>")
        else:
            # Execute file
            runtime.execute_file(sys.argv[1])
    else:
        # Demo mode
        demo_code = """
# Demo Python Simpler
cetak("=== DEMO PYTHON SIMPLER ===")

# Basic operations
nama = masukan("Siapa nama Anda? ")
cetak("Halo,", nama)

# List operations
angka = daftar([1, 2, 3, 4, 5])
cetak("Daftar angka:", angka)
tambah(angka, 6)
cetak("Setelah menambah 6:", angka)
cetak("Total:", jumlah(angka))
cetak("Maksimum:", maksimum(angka))

# String operations
teks = "Python Simpler adalah Luar Biasa"
cetak("Teks asli:", teks)
cetak("Huruf besar:", huruf_besar(teks))
kata_kata = pisah(teks, " ")
cetak("Dipecah menjadi:", kata_kata)

# Control flow
cetak("\\nAngka genap dari 1-10:")
untuk i dalam rentang(1, 11):
    jika i % 2 == 0:
        cetak(i, "adalah genap")

# Dictionary
data = kamus({"nama": "Alice", "umur": 25, "kota": "Jakarta"})
cetak("\\nData:", data)
untuk kunci, nilai dalam item(data):
    cetak(f"{kunci}: {nilai}")

cetak("\\n=== SELESAI ===")
        """
        
        print("🚀 Running Python Simpler Demo...")
        runtime.execute_code(demo_code)
        
        print("\n" + "="*50)
        print("PERFORMANCE STATS:")
        stats = runtime.translator.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
