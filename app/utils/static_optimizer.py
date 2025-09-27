"""
Optimizador de archivos estáticos para Synapsis Apoyos
Incluye compresión, minificación, versionado y gestión de CDN
"""

import os
import hashlib
import gzip
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

try:
    import cssmin
    import jsmin
    from PIL import Image
    import brotli
except ImportError:
    cssmin = None
    jsmin = None
    Image = None
    brotli = None

logger = logging.getLogger(__name__)

class StaticOptimizer:
    """Optimizador de archivos estáticos"""
    
    def __init__(self, static_dir: str, output_dir: str = None):
        self.static_dir = Path(static_dir)
        self.output_dir = Path(output_dir) if output_dir else self.static_dir / 'optimized'
        self.manifest_file = self.output_dir / 'manifest.json'
        self.manifest = {}
        self.compression_enabled = True
        self.minification_enabled = True
        self.image_optimization_enabled = True
        
        # Configuración de compresión
        self.gzip_level = 9
        self.brotli_quality = 11
        
        # Configuración de imágenes
        self.image_quality = 85
        self.image_formats = {'.jpg', '.jpeg', '.png', '.webp'}
        self.max_image_size = (1920, 1080)
        
        # Archivos a procesar
        self.css_extensions = {'.css'}
        self.js_extensions = {'.js'}
        self.compressible_extensions = {'.css', '.js', '.html', '.json', '.xml', '.txt', '.svg'}
        
        # Crear directorio de salida
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar manifest existente
        self._load_manifest()
    
    def _load_manifest(self):
        """Cargar manifest de archivos procesados"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    self.manifest = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando manifest: {e}")
                self.manifest = {}
    
    def _save_manifest(self):
        """Guardar manifest de archivos procesados"""
        try:
            with open(self.manifest_file, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando manifest: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Obtener hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()[:8]
        except Exception as e:
            logger.error(f"Error calculando hash de {file_path}: {e}")
            return str(int(time.time()))[:8]
    
    def _get_versioned_filename(self, file_path: Path, content_hash: str) -> str:
        """Generar nombre de archivo con versión"""
        stem = file_path.stem
        suffix = file_path.suffix
        return f"{stem}.{content_hash}{suffix}"
    
    def _minify_css(self, content: str) -> str:
        """Minificar CSS"""
        if not cssmin:
            logger.warning("cssmin no disponible, omitiendo minificación CSS")
            return content
        
        try:
            return cssmin.cssmin(content)
        except Exception as e:
            logger.error(f"Error minificando CSS: {e}")
            return content
    
    def _minify_js(self, content: str) -> str:
        """Minificar JavaScript"""
        if not jsmin:
            logger.warning("jsmin no disponible, omitiendo minificación JS")
            return content
        
        try:
            return jsmin.jsmin(content)
        except Exception as e:
            logger.error(f"Error minificando JS: {e}")
            return content
    
    def _optimize_image(self, input_path: Path, output_path: Path) -> bool:
        """Optimizar imagen"""
        if not Image:
            logger.warning("PIL no disponible, omitiendo optimización de imágenes")
            shutil.copy2(input_path, output_path)
            return True
        
        try:
            with Image.open(input_path) as img:
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Redimensionar si es necesario
                if img.size[0] > self.max_image_size[0] or img.size[1] > self.max_image_size[1]:
                    img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                
                # Guardar optimizada
                save_kwargs = {'optimize': True}
                if input_path.suffix.lower() in {'.jpg', '.jpeg'}:
                    save_kwargs['quality'] = self.image_quality
                    save_kwargs['format'] = 'JPEG'
                elif input_path.suffix.lower() == '.png':
                    save_kwargs['format'] = 'PNG'
                
                img.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            logger.error(f"Error optimizando imagen {input_path}: {e}")
            shutil.copy2(input_path, output_path)
            return False
    
    def _compress_file(self, file_path: Path, content: bytes = None) -> Dict[str, Path]:
        """Comprimir archivo con gzip y brotli"""
        compressed_files = {}
        
        if content is None:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error leyendo archivo {file_path}: {e}")
                return compressed_files
        
        # Compresión gzip
        try:
            gzip_path = file_path.with_suffix(file_path.suffix + '.gz')
            with gzip.open(gzip_path, 'wb', compresslevel=self.gzip_level) as f:
                f.write(content)
            compressed_files['gzip'] = gzip_path
        except Exception as e:
            logger.error(f"Error comprimiendo con gzip {file_path}: {e}")
        
        # Compresión brotli
        if brotli:
            try:
                brotli_path = file_path.with_suffix(file_path.suffix + '.br')
                compressed_content = brotli.compress(content, quality=self.brotli_quality)
                with open(brotli_path, 'wb') as f:
                    f.write(compressed_content)
                compressed_files['brotli'] = brotli_path
            except Exception as e:
                logger.error(f"Error comprimiendo con brotli {file_path}: {e}")
        
        return compressed_files
    
    def process_file(self, file_path: Path, relative_path: Path) -> Dict:
        """Procesar un archivo individual"""
        file_info = {
            'original': str(relative_path),
            'optimized': None,
            'compressed': {},
            'size_original': 0,
            'size_optimized': 0,
            'compression_ratio': 0,
            'hash': '',
            'processed_at': datetime.now().isoformat()
        }
        
        try:
            # Obtener tamaño original
            file_info['size_original'] = file_path.stat().st_size
            
            # Leer contenido original
            if file_path.suffix.lower() in self.image_formats:
                # Procesar imagen
                content_hash = self._get_file_hash(file_path)
                versioned_name = self._get_versioned_filename(relative_path, content_hash)
                output_path = self.output_dir / versioned_name
                
                if self.image_optimization_enabled:
                    self._optimize_image(file_path, output_path)
                else:
                    shutil.copy2(file_path, output_path)
                
                file_info['optimized'] = str(versioned_name)
                file_info['hash'] = content_hash
                
            else:
                # Procesar archivo de texto
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Minificar si es necesario
                if self.minification_enabled:
                    if file_path.suffix.lower() in self.css_extensions:
                        content = self._minify_css(content)
                    elif file_path.suffix.lower() in self.js_extensions:
                        content = self._minify_js(content)
                
                # Generar hash del contenido procesado
                content_bytes = content.encode('utf-8')
                content_hash = hashlib.md5(content_bytes).hexdigest()[:8]
                
                # Crear nombre versionado
                versioned_name = self._get_versioned_filename(relative_path, content_hash)
                output_path = self.output_dir / versioned_name
                
                # Crear directorio padre si no existe
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Guardar archivo optimizado
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                file_info['optimized'] = str(versioned_name)
                file_info['hash'] = content_hash
                
                # Comprimir si está habilitado
                if self.compression_enabled and file_path.suffix.lower() in self.compressible_extensions:
                    compressed_files = self._compress_file(output_path, content_bytes)
                    for comp_type, comp_path in compressed_files.items():
                        file_info['compressed'][comp_type] = str(comp_path.relative_to(self.output_dir))
            
            # Calcular tamaño optimizado y ratio de compresión
            if file_info['optimized']:
                optimized_path = self.output_dir / file_info['optimized']
                if optimized_path.exists():
                    file_info['size_optimized'] = optimized_path.stat().st_size
                    if file_info['size_original'] > 0:
                        file_info['compression_ratio'] = (
                            1 - file_info['size_optimized'] / file_info['size_original']
                        ) * 100
            
        except Exception as e:
            logger.error(f"Error procesando archivo {file_path}: {e}")
        
        return file_info
    
    def optimize_directory(self, directory: Path = None) -> Dict:
        """Optimizar todos los archivos en un directorio"""
        if directory is None:
            directory = self.static_dir
        
        results = {
            'processed_files': {},
            'total_files': 0,
            'total_size_original': 0,
            'total_size_optimized': 0,
            'total_compression_ratio': 0,
            'processing_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Encontrar todos los archivos a procesar
            files_to_process = []
            for file_path in directory.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    files_to_process.append(file_path)
            
            results['total_files'] = len(files_to_process)
            
            # Procesar cada archivo
            for file_path in files_to_process:
                try:
                    relative_path = file_path.relative_to(directory)
                    file_info = self.process_file(file_path, relative_path)
                    
                    results['processed_files'][str(relative_path)] = file_info
                    results['total_size_original'] += file_info['size_original']
                    results['total_size_optimized'] += file_info['size_optimized']
                    
                except Exception as e:
                    error_msg = f"Error procesando {file_path}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Calcular ratio de compresión total
            if results['total_size_original'] > 0:
                results['total_compression_ratio'] = (
                    1 - results['total_size_optimized'] / results['total_size_original']
                ) * 100
            
            # Actualizar manifest
            self.manifest.update(results['processed_files'])
            self._save_manifest()
            
        except Exception as e:
            error_msg = f"Error optimizando directorio {directory}: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        results['processing_time'] = time.time() - start_time
        return results
    
    def get_static_url(self, original_path: str) -> str:
        """Obtener URL optimizada para un archivo estático"""
        if original_path in self.manifest:
            optimized_path = self.manifest[original_path].get('optimized')
            if optimized_path:
                return f"/static/optimized/{optimized_path}"
        
        # Fallback a archivo original
        return f"/static/{original_path}"
    
    def clean_old_files(self, max_age_days: int = 30):
        """Limpiar archivos optimizados antiguos"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_files = []
        
        try:
            for file_path in self.output_dir.rglob('*'):
                if file_path.is_file():
                    # Verificar si el archivo está en el manifest
                    file_in_manifest = False
                    for file_info in self.manifest.values():
                        if (file_info.get('optimized') == str(file_path.relative_to(self.output_dir)) or
                            str(file_path.relative_to(self.output_dir)) in file_info.get('compressed', {}).values()):
                            file_in_manifest = True
                            break
                    
                    # Si no está en el manifest o es muy antiguo, eliminarlo
                    if not file_in_manifest:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_path.unlink()
                            cleaned_files.append(str(file_path))
            
        except Exception as e:
            logger.error(f"Error limpiando archivos antiguos: {e}")
        
        return cleaned_files
    
    def generate_report(self) -> Dict:
        """Generar reporte de optimización"""
        report = {
            'summary': {
                'total_files': len(self.manifest),
                'total_size_original': 0,
                'total_size_optimized': 0,
                'total_compression_ratio': 0,
                'space_saved': 0
            },
            'by_type': {},
            'top_compressed': [],
            'errors': []
        }
        
        # Calcular estadísticas
        for file_path, file_info in self.manifest.items():
            file_ext = Path(file_path).suffix.lower()
            
            # Estadísticas por tipo
            if file_ext not in report['by_type']:
                report['by_type'][file_ext] = {
                    'count': 0,
                    'size_original': 0,
                    'size_optimized': 0,
                    'compression_ratio': 0
                }
            
            type_stats = report['by_type'][file_ext]
            type_stats['count'] += 1
            type_stats['size_original'] += file_info['size_original']
            type_stats['size_optimized'] += file_info['size_optimized']
            
            # Estadísticas generales
            report['summary']['total_size_original'] += file_info['size_original']
            report['summary']['total_size_optimized'] += file_info['size_optimized']
            
            # Top archivos más comprimidos
            if file_info['compression_ratio'] > 0:
                report['top_compressed'].append({
                    'file': file_path,
                    'compression_ratio': file_info['compression_ratio'],
                    'size_saved': file_info['size_original'] - file_info['size_optimized']
                })
        
        # Calcular ratios de compresión
        if report['summary']['total_size_original'] > 0:
            report['summary']['total_compression_ratio'] = (
                1 - report['summary']['total_size_optimized'] / report['summary']['total_size_original']
            ) * 100
            report['summary']['space_saved'] = (
                report['summary']['total_size_original'] - report['summary']['total_size_optimized']
            )
        
        for file_ext, type_stats in report['by_type'].items():
            if type_stats['size_original'] > 0:
                type_stats['compression_ratio'] = (
                    1 - type_stats['size_optimized'] / type_stats['size_original']
                ) * 100
        
        # Ordenar top comprimidos
        report['top_compressed'].sort(key=lambda x: x['compression_ratio'], reverse=True)
        report['top_compressed'] = report['top_compressed'][:10]
        
        return report


class CDNManager:
    """Gestor de CDN para archivos estáticos"""
    
    def __init__(self, cdn_url: str = None, local_fallback: bool = True):
        self.cdn_url = cdn_url.rstrip('/') if cdn_url else None
        self.local_fallback = local_fallback
        self.cache_busting = True
        
    def get_asset_url(self, asset_path: str, version: str = None) -> str:
        """Obtener URL de asset con CDN o fallback local"""
        # Limpiar path
        asset_path = asset_path.lstrip('/')
        
        # Agregar cache busting si está habilitado
        if self.cache_busting and version:
            if '?' in asset_path:
                asset_path += f"&v={version}"
            else:
                asset_path += f"?v={version}"
        
        # Usar CDN si está configurado
        if self.cdn_url:
            return f"{self.cdn_url}/{asset_path}"
        
        # Fallback local
        return f"/static/{asset_path}"
    
    def generate_preload_links(self, assets: List[str]) -> List[str]:
        """Generar enlaces de precarga para assets críticos"""
        preload_links = []
        
        for asset in assets:
            asset_url = self.get_asset_url(asset)
            
            # Determinar tipo de recurso
            if asset.endswith('.css'):
                rel_type = 'stylesheet'
                as_type = 'style'
            elif asset.endswith('.js'):
                rel_type = 'preload'
                as_type = 'script'
            elif asset.endswith(('.woff', '.woff2')):
                rel_type = 'preload'
                as_type = 'font'
            elif asset.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                rel_type = 'preload'
                as_type = 'image'
            else:
                continue
            
            if rel_type == 'stylesheet':
                preload_links.append(f'<link rel="stylesheet" href="{asset_url}">')
            else:
                preload_links.append(f'<link rel="{rel_type}" as="{as_type}" href="{asset_url}">')
        
        return preload_links


def setup_static_optimization(app):
    """Configurar optimización de archivos estáticos en Flask"""
    static_optimizer = StaticOptimizer(
        static_dir=app.static_folder,
        output_dir=os.path.join(app.static_folder, 'optimized')
    )
    
    cdn_manager = CDNManager(
        cdn_url=app.config.get('CDN_URL'),
        local_fallback=True
    )
    
    # Agregar funciones al contexto de templates
    @app.context_processor
    def inject_static_helpers():
        return {
            'static_optimized': static_optimizer.get_static_url,
            'cdn_asset': cdn_manager.get_asset_url,
            'preload_assets': cdn_manager.generate_preload_links
        }
    
    # Comando CLI para optimizar archivos
    @app.cli.command()
    def optimize_static():
        """Optimizar archivos estáticos"""
        click.echo("Optimizando archivos estáticos...")
        results = static_optimizer.optimize_directory()
        
        click.echo(f"Archivos procesados: {results['total_files']}")
        click.echo(f"Tamaño original: {results['total_size_original'] / 1024:.2f} KB")
        click.echo(f"Tamaño optimizado: {results['total_size_optimized'] / 1024:.2f} KB")
        click.echo(f"Compresión: {results['total_compression_ratio']:.2f}%")
        click.echo(f"Tiempo: {results['processing_time']:.2f}s")
        
        if results['errors']:
            click.echo(f"Errores: {len(results['errors'])}")
            for error in results['errors']:
                click.echo(f"  - {error}")
    
    return static_optimizer, cdn_manager