import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

@Component({ template: '' })
class PantallaLogin {}

describe('authInterceptor', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    sessionStorage.clear();

    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'login', component: PantallaLogin }]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    sessionStorage.clear();
  });

  it('agrega el encabezado Authorization cuando hay token', () => {
    sessionStorage.setItem('tecnostock.token', 'abc.def.ghi');

    TestBed.inject(AuthService)
      .refrescarUsuario()
      .subscribe({ error: () => undefined });

    const peticion = http.expectOne((req) => req.url.endsWith('/auth/me'));
    expect(peticion.request.headers.get('Authorization')).toBe('Bearer abc.def.ghi');
    peticion.flush({
      usuario_id: 1,
      nombre_usuario: 'admin',
      nombre_completo: 'Administrador',
      activo: true,
      fecha_creacion: '2026-01-01T00:00:00',
    });
  });

  it('no agrega Authorization cuando no hay sesión', () => {
    TestBed.inject(AuthService)
      .refrescarUsuario()
      .subscribe({ error: () => undefined });

    const peticion = http.expectOne((req) => req.url.endsWith('/auth/me'));
    expect(peticion.request.headers.has('Authorization')).toBe(false);
    peticion.flush({}, { status: 401, statusText: 'Unauthorized' });
  });

  it('cierra la sesión y redirige al login ante un 401', () => {
    sessionStorage.setItem('tecnostock.token', 'token.expirado');
    sessionStorage.setItem(
      'tecnostock.usuario',
      JSON.stringify({ usuario_id: 1, nombre_usuario: 'admin' }),
    );

    const router = TestBed.inject(Router);
    const navegar = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    TestBed.inject(AuthService)
      .refrescarUsuario()
      .subscribe({ error: () => undefined });

    const peticion = http.expectOne((req) => req.url.endsWith('/auth/me'));
    peticion.flush(
      { detail: 'Token inválido', code: 'token_invalido' },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(navegar).toHaveBeenCalledWith(['/login']);
    expect(sessionStorage.getItem('tecnostock.token')).toBeNull();
  });

  it('no cierra la sesión ante un 401 del propio login', () => {
    const router = TestBed.inject(Router);
    const navegar = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    TestBed.inject(AuthService)
      .login('admin', 'incorrecta')
      .subscribe({ error: () => undefined });

    const peticion = http.expectOne((req) => req.url.endsWith('/auth/login'));
    peticion.flush({}, { status: 401, statusText: 'Unauthorized' });

    // El servicio limpia la sesión, pero el interceptor no debe navegar:
    // la pantalla de login muestra el error en el formulario.
    expect(navegar).not.toHaveBeenCalled();
  });
});
