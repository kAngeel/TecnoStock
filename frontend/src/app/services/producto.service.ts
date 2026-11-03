import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Producto, ProductoPayload, StockBajo } from '../core/models';

export interface FiltrosProducto {
  busqueda?: string;
  categoriaId?: number | null;
  soloActivos?: boolean;
}

@Injectable({ providedIn: 'root' })
export class ProductoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/productos`;

  listar(filtros: FiltrosProducto = {}): Observable<Producto[]> {
    let params = new HttpParams();
    if (filtros.busqueda?.trim()) {
      params = params.set('busqueda', filtros.busqueda.trim());
    }
    if (filtros.categoriaId) {
      params = params.set('categoria_id', String(filtros.categoriaId));
    }
    if (filtros.soloActivos !== undefined) {
      params = params.set('solo_activos', String(filtros.soloActivos));
    }
    return this.http.get<Producto[]>(this.base, { params });
  }

  obtener(productoId: number): Observable<Producto> {
    return this.http.get<Producto>(`${this.base}/${productoId}`);
  }

  crear(payload: ProductoPayload): Observable<Producto> {
    return this.http.post<Producto>(this.base, payload);
  }

  actualizar(productoId: number, payload: ProductoPayload): Observable<Producto> {
    return this.http.put<Producto>(`${this.base}/${productoId}`, payload);
  }

  desactivar(productoId: number): Observable<Producto> {
    return this.http.patch<Producto>(`${this.base}/${productoId}/desactivar`, {});
  }

  activar(productoId: number): Observable<Producto> {
    return this.http.patch<Producto>(`${this.base}/${productoId}/activar`, {});
  }

  stockBajo(): Observable<StockBajo[]> {
    return this.http.get<StockBajo[]>(`${this.base}/stock-bajo`);
  }

  valorInventario(): Observable<Record<string, number>> {
    return this.http.get<Record<string, number>>(`${this.base}/valor-inventario`);
  }
}
