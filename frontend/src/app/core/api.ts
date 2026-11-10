import { HttpErrorResponse } from '@angular/common/http';

import { ErrorApi } from './models';

/** Extrae un mensaje claro del cuerpo de error de la API. */
export function mensajeError(
  error: unknown,
  porDefecto = 'No se pudo completar la operación. Intente nuevamente.',
): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verifique que la API esté en ejecución.';
    }

    const cuerpo = error.error as ErrorApi | null;
    if (cuerpo && typeof cuerpo === 'object' && typeof cuerpo.detail === 'string') {
      return cuerpo.detail;
    }

    if (error.status === 401) {
      return 'La sesión no es válida o expiró. Vuelva a iniciar sesión.';
    }
    if (error.status === 403) {
      return 'No tiene permisos para realizar esta operación.';
    }
    if (error.status === 422) {
      return 'Los datos enviados no son válidos.';
    }
    if (error.status >= 500) {
      return 'Ocurrió un error en el servidor. Intente nuevamente en unos instantes.';
    }
  }

  return porDefecto;
}

/**
 * Mensaje para el formulario de login.
 *
 * Un 401 en el login significa credenciales incorrectas, no una sesión
 * caducada ni un problema de conexión: no debe reutilizar el texto genérico
 * de "sesión no válida" ni el de fallo de red (reservado a status 0).
 */
export function mensajeErrorLogin(error: unknown): string {
  const porDefecto = 'Usuario o contraseña incorrectos.';

  if (error instanceof HttpErrorResponse) {
    // Usuario inactivo: el backend envía un detalle distinto y útil.
    if (error.status === 403) {
      return mensajeError(error, porDefecto);
    }
    if (error.status === 401) {
      return porDefecto;
    }
  }

  return mensajeError(error, porDefecto);
}
