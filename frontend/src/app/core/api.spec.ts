import { HttpErrorResponse } from '@angular/common/http';

import { mensajeError, mensajeErrorLogin } from './api';

function errorHttp(status: number, body: unknown = null): HttpErrorResponse {
  return new HttpErrorResponse({
    status,
    statusText: status === 401 ? 'Unauthorized' : 'Error',
    error: body,
    url: 'http://localhost:8000/api/auth/login',
  });
}

describe('mensajeErrorLogin', () => {
  it('un 401 muestra credenciales incorrectas, no un problema de sesión', () => {
    const mensaje = mensajeErrorLogin(
      errorHttp(401, {
        detail: 'Usuario o contraseña incorrectos.',
        code: 'credenciales_invalidas',
      }),
    );

    expect(mensaje).toBe('Usuario o contraseña incorrectos.');
  });

  it('un 401 sin cuerpo tampoco se presenta como sesión caducada', () => {
    const mensaje = mensajeErrorLogin(errorHttp(401));

    expect(mensaje).toBe('Usuario o contraseña incorrectos.');
    expect(mensaje).not.toContain('sesión');
    expect(mensaje).not.toContain('conectar');
  });

  it('un 403 conserva el detalle del backend (usuario inactivo)', () => {
    const mensaje = mensajeErrorLogin(
      errorHttp(403, {
        detail: 'El usuario está inactivo. Contacte al administrador.',
        code: 'usuario_inactivo',
      }),
    );

    expect(mensaje).toBe('El usuario está inactivo. Contacte al administrador.');
  });

  it('un status 0 sí se presenta como error de conexión', () => {
    const mensaje = mensajeErrorLogin(errorHttp(0));

    expect(mensaje).toContain('No se pudo conectar con el servidor');
  });

  it('un 500 se presenta como error del servidor', () => {
    const mensaje = mensajeErrorLogin(errorHttp(500));

    expect(mensaje).toContain('error en el servidor');
  });

  it('mensajeError sigue usando el texto de sesión para un 401 fuera del login', () => {
    const mensaje = mensajeError(errorHttp(401), 'otro');

    expect(mensaje).toBe('La sesión no es válida o expiró. Vuelva a iniciar sesión.');
  });
});
