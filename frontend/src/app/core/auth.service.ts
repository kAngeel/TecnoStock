import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { catchError, map, Observable, tap, throwError } from 'rxjs';

import { environment } from '../../environments/environment';
import { TokenResponse, Usuario } from './models';

const TOKEN_KEY = 'tecnostock.token';
const USUARIO_KEY = 'tecnostock.usuario';

function leerUsuario(): Usuario | null {
  try {
    const texto = sessionStorage.getItem(USUARIO_KEY);
    return texto ? (JSON.parse(texto) as Usuario) : null;
  } catch {
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly _usuario = signal<Usuario | null>(leerUsuario());
  readonly usuario = this._usuario.asReadonly();

  readonly autenticado = computed(() => this._usuario() !== null && !!this.token());

  token(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  nombreUsuario(): string {
    return this._usuario()?.nombre_completo || this._usuario()?.nombre_usuario || '';
  }

  login(nombreUsuario: string, contrasena: string): Observable<Usuario> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, {
        nombre_usuario: nombreUsuario,
        contrasena,
      })
      .pipe(
        tap((respuesta) => {
          try {
            sessionStorage.setItem(TOKEN_KEY, respuesta.access_token);
            sessionStorage.setItem(USUARIO_KEY, JSON.stringify(respuesta.usuario));
          } catch {
            // Si el navegador bloquea sessionStorage, la sesión vive en memoria.
          }
          this._usuario.set(respuesta.usuario);
        }),
        map((respuesta) => respuesta.usuario),
        catchError((error: unknown) => {
          // Un intento fallido no deja sesión previa activa.
          this.limpiar();
          return throwError(() => error);
        }),
      );
  }

  /** Recupera el usuario desde la API (por ejemplo al recargar la página). */
  refrescarUsuario(): Observable<Usuario> {
    return this.http
      .get<Usuario>(`${environment.apiUrl}/auth/me`)
      .pipe(tap((usuario) => this._usuario.set(usuario)));
  }

  cerrarSesion(): void {
    this.limpiar();
    void this.router.navigate(['/login']);
  }

  private limpiar(): void {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USUARIO_KEY);
    } catch {
      // Sin sessionStorage no hay nada que limpiar.
    }
    this._usuario.set(null);
  }
}
