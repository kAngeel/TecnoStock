import { errorDe } from './form-utils';

function campo(touched: boolean, mensajes: Array<string | undefined>) {
  return {
    touched: () => touched,
    errors: () => mensajes.map((message) => ({ kind: 'test', message })),
  };
}

describe('errorDe', () => {
  it('no muestra errores hasta que el campo fue tocado', () => {
    expect(errorDe(campo(false, ['Campo obligatorio']))).toBeNull();
  });

  it('devuelve el primer mensaje cuando el campo fue tocado', () => {
    expect(errorDe(campo(true, ['Campo obligatorio', 'Otro error']))).toBe('Campo obligatorio');
  });

  it('devuelve null cuando el campo tocado no tiene errores', () => {
    expect(errorDe(campo(true, []))).toBeNull();
  });

  it('usa un mensaje por defecto si el error no trae texto', () => {
    expect(errorDe(campo(true, [undefined]))).toBe('Valor inválido.');
  });
});
