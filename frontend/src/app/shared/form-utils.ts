/**
 * Forma mínima que necesita un campo de Signal Forms para mostrar su error.
 * Se declara estructuralmente para no depender de la varianza de `FieldState<T>`.
 */
interface CampoConErrores {
  touched(): boolean;
  errors(): ReadonlyArray<{ message?: string }>;
}

/**
 * Devuelve el primer mensaje de error visible de un campo de Signal Forms.
 * Solo muestra errores cuando el campo ya fue tocado (o se intentó enviar).
 */
export function errorDe(campo: CampoConErrores): string | null {
  if (!campo.touched()) {
    return null;
  }

  const errores = campo.errors();
  if (errores.length === 0) {
    return null;
  }

  return errores[0].message ?? 'Valor inválido.';
}
