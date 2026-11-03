import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Categoria, CategoriaPayload } from '../core/models';

@Injectable({ providedIn: 'root' })
export class CategoriaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/categorias`;

  listar(): Observable<Categoria[]> {
    return this.http.get<Categoria[]>(this.base);
  }

  crear(payload: CategoriaPayload): Observable<Categoria> {
    return this.http.post<Categoria>(this.base, payload);
  }

  actualizar(categoriaId: number, payload: CategoriaPayload): Observable<Categoria> {
    return this.http.put<Categoria>(`${this.base}/${categoriaId}`, payload);
  }
}
