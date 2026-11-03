import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';

import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';
import { TokenResponse, Usuario } from './models';

const USUARIO: Usuario = {
  usuario_id: 1,
  nombre_usuario: 'admin',
  nombre_completo: 'Administrador del Sistema',
  activo: true,
  fecha_creacion: '2026-01-01T00:00:00',
};

const RESPUESTA: TokenResponse = {
  access_token: 'cabecera.cuerpo.firma',
  token_type: 'bearer',
  expires_in: 3600,
  usuario: USUARIO,
};

describe('AuthService', () => {
  let servicio: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    sessionStorage.clear();

    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });

    servicio = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    sessionStorage.clear();
  });

  it('inicia sin sesión cuando no hay token almacenado', () => {
    expect(servicio.token()).toBeNull();
    expect(servicio.usuario()).toBeNull();
    expect(servicio.autenticado()).toBe(false);
  });

  it('guarda el token y el usuario en sessionStorage al iniciar sesión', () => {
    let usuarioRecibido: Usuario | undefined;

    servicio.login('admin', 'TecnoStock2026').subscribe((usuario) => {
      usuarioRecibido = usuario;
    });

    const peticion = http.expectOne(`${environment.apiUrl}/auth/login`);
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({
      nombre_usuario: 'admin',
      contrasena: 'TecnoStock2026',
    });

    peticion.flush(RESPUESTA);

    expect(usuarioRecibido?.nombre_usuario).toBe('admin');
    expect(servicio.token()).toBe(RESPUESTA.access_token);
    expect(servicio.usuario()?.nombre_completo).toBe('Administrador del Sistema');
    expect(servicio.nombreUsuario()).toBe('Administrador del Sistema');
    expect(servicio.autenticado()).toBe(true);

    // El token vive en sessionStorage, nunca en localStorage.
    expect(sessionStorage.getItem('tecnostock.token')).toBe(RESPUESTA.access_token);
    expect(localStorage.getItem('tecnostock.token')).toBeNull();
  });

  it('no conserva sesión cuando las credenciales son rechazadas', () => {
    let fallo = false;

    servicio.login('admin', 'incorrecta').subscribe({
      error: () => {
        fallo = true;
      },
    });

    const peticion = http.expectOne(`${environment.apiUrl}/auth/login`);
    peticion.flush(
      { detail: 'Usuario o contraseña incorrectos.', code: 'credenciales_invalidas' },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(fallo).toBe(true);
    expect(servicio.token()).toBeNull();
    expect(servicio.usuario()).toBeNull();
    expect(servicio.autenticado()).toBe(false);
  });

  it('recupera el usuario autenticado desde la API', () => {
    servicio.refrescarUsuario().subscribe();

    const peticion = http.expectOne(`${environment.apiUrl}/auth/me`);
    expect(peticion.request.method).toBe('GET');
    peticion.flush(USUARIO);

    expect(servicio.usuario()?.usuario_id).toBe(1);
  });

  it('limpia la sesión al cerrar sesión', () => {
    sessionStorage.setItem('tecnostock.token', 'token.previo');
    sessionStorage.setItem('tecnostock.usuario', JSON.stringify(USUARIO));

    const router = TestBed.inject(Router);
    const navegar = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    servicio.cerrarSesion();

    expect(servicio.token()).toBeNull();
    expect(sessionStorage.getItem('tecnostock.token')).toBeNull();
    expect(sessionStorage.getItem('tecnostock.usuario')).toBeNull();
    expect(navegar).toHaveBeenCalledWith(['/login']);
  });
});
