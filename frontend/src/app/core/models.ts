/** Contratos de datos que expone la API de TecnoStock. */

export interface Usuario {
  usuario_id: number;
  nombre_usuario: string;
  nombre_completo: string;
  activo: boolean;
  fecha_creacion: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  usuario: Usuario;
}

export interface Categoria {
  categoria_id: number;
  nombre: string;
  descripcion: string | null;
  total_productos: number;
}

export interface CategoriaPayload {
  nombre: string;
  descripcion: string | null;
}

export interface Producto {
  producto_id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  categoria_id: number;
  categoria_nombre: string;
  precio_compra: number;
  precio_venta: number;
  stock: number;
  stock_minimo: number;
  activo: boolean;
  fecha_creacion: string;
  fecha_actualizacion: string;
  valor_inventario: number;
  stock_bajo: boolean;
}

export interface ProductoPayload {
  codigo: string;
  nombre: string;
  descripcion: string;
  categoria_id: number;
  precio_compra: number;
  precio_venta: number;
  stock_minimo: number;
  activo: boolean;
}

export interface StockBajo {
  producto_id: number;
  codigo: string;
  nombre: string;
  categoria_id: number;
  categoria_nombre: string;
  stock: number;
  stock_minimo: number;
  faltante: number;
  precio_compra: number;
}

export type TipoMovimiento = 'ENTRADA' | 'SALIDA';

export interface Movimiento {
  movimiento_id: number;
  producto_id: number;
  producto_codigo: string;
  producto_nombre: string;
  usuario_id: number;
  nombre_usuario: string;
  usuario_nombre_completo: string;
  tipo: TipoMovimiento;
  cantidad: number;
  motivo: string;
  stock_anterior: number;
  stock_posterior: number;
  fecha: string;
}

export interface MovimientoPage {
  items: Movimiento[];
  total: number;
  pagina: number;
  tamano_pagina: number;
  total_paginas: number;
}

export interface MovimientoPayload {
  producto_id: number;
  cantidad: number;
  motivo: string;
}

export interface MovimientoRegistrado {
  movimiento_id: number;
  producto_id: number;
  tipo: TipoMovimiento;
  cantidad: number;
  stock_anterior: number;
  stock_posterior: number;
}

export interface DashboardResumen {
  productos_activos: number;
  productos_inactivos: number;
  productos_total: number;
  categorias_total: number;
  productos_stock_bajo: number;
  valor_inventario: number;
  unidades_en_stock: number;
  movimientos_periodo: number;
  unidades_entrada: number;
  unidades_salida: number;
}

export interface MovimientoPorDia {
  fecha: string;
  unidades_entrada: number;
  unidades_salida: number;
  movimientos: number;
}

export interface TopProducto {
  producto_id: number;
  codigo: string;
  nombre: string;
  unidades_entrada: number;
  unidades_salida: number;
  movimientos: number;
}

export interface UltimoMovimiento {
  movimiento_id: number;
  fecha: string;
  tipo: TipoMovimiento;
  cantidad: number;
  motivo: string;
  stock_anterior: number;
  stock_posterior: number;
  producto_codigo: string;
  producto_nombre: string;
  nombre_usuario: string;
}

export interface Dashboard {
  fecha_desde: string;
  fecha_hasta: string;
  resumen: DashboardResumen;
  serie_diaria: MovimientoPorDia[];
  top_productos: TopProducto[];
  ultimos_movimientos: UltimoMovimiento[];
}

export interface ErrorApi {
  detail?: string;
  code?: string;
  details?: Array<{ campo?: string | null; mensaje?: string }> | unknown;
}
