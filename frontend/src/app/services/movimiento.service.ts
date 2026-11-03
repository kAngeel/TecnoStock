import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  MovimientoPage,
  MovimientoPayload,
  MovimientoRegistrado,
  TipoMovimiento,
} from '../core/models';

export interface FiltrosMovimiento {
  fechaDesde?: string | null;
  fechaHasta?: string | null;
  productoId?: number | null;
  tipo?: TipoMovimiento | null;
  pagina?: number;
  tamanoPagina?: number;
}

@Injectable({ providedIn: 'root' })
export class MovimientoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/movimientos`;

  registrarEntrada(payload: MovimientoPayload): Observable<MovimientoRegistrado> {
    return this.http.post<MovimientoRegistrado>(`${this.base}/entradas`, payload);
  }

  registrarSalida(payload: MovimientoPayload): Observable<MovimientoRegistrado> {
    return this.http.post<MovimientoRegistrado>(`${this.base}/salidas`, payload);
  }

  listar(filtros: FiltrosMovimiento = {}): Observable<MovimientoPage> {
    let params = new HttpParams();

    if (filtros.fechaDesde) params = params.set('fecha_desde', filtros.fechaDesde);
    if (filtros.fechaHasta) params = params.set('fecha_hasta', filtros.fechaHasta);
    if (filtros.productoId) params = params.set('producto_id', String(filtros.productoId));
    if (filtros.tipo) params = params.set('tipo', filtros.tipo);

    params = params
      .set('pagina', String(filtros.pagina ?? 1))
      .set('tamano_pagina', String(filtros.tamanoPagina ?? 15));

    return this.http.get<MovimientoPage>(this.base, { params });
  }
}
