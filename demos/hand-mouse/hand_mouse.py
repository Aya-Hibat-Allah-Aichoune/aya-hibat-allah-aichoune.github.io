import cv2
import mediapipe as mp
import math
import pyautogui

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True

ANCHO_PANTALLA, ALTO_PANTALLA = pyautogui.size()

MARGEN = 0.2

RATIO_PINZA_ON = 0.30
RATIO_PINZA_OFF = 0.40

SUAVIZADO = 0.35

FACTOR_DEDO_EXTENDIDO = 1.25

FRAMES_CAMBIO_MODO = 4

SCROLL_SENSIBILIDAD = 60
SCROLL_ZONA_MUERTA = 0.003

ESTADO_CURSOR = "CURSOR"
ESTADO_SCROLL = "SCROLL"
ESTADO_PAUSA = "PAUSA"

DEDOS = {
    "indice": (8, 6),
    "corazon": (12, 10),
    "anular": (16, 14),
    "menique": (20, 18),
}


def distancia(a, b, w, h):
    return math.hypot((a.x - b.x) * w, (a.y - b.y) * h)


def calcular_ratio_pinza(lm, w, h, punta_dedo):
    pulgar = lm.landmark[4]
    dedo = lm.landmark[punta_dedo]
    muneca = lm.landmark[0]
    nudillo = lm.landmark[9]

    tam_mano = distancia(muneca, nudillo, w, h)
    return distancia(pulgar, dedo, w, h) / tam_mano if tam_mano > 0 else 999


def dedos_extendidos(lm, w, h):
    muneca = lm.landmark[0]
    resultado = {}
    for nombre, (punta, medio) in DEDOS.items():
        d_punta = distancia(lm.landmark[punta], muneca, w, h)
        d_medio = distancia(lm.landmark[medio], muneca, w, h)
        resultado[nombre] = d_punta > d_medio * FACTOR_DEDO_EXTENDIDO
    return resultado


def detectar_pose(dedos):
    if not any(dedos.values()):
        return ESTADO_PAUSA
    if dedos["indice"] and dedos["corazon"] and not dedos["anular"] and not dedos["menique"]:
        return ESTADO_SCROLL
    return ESTADO_CURSOR


def punto_control(lm):
    pulgar = lm.landmark[4]
    indice = lm.landmark[8]
    return (pulgar.x + indice.x) / 2, (pulgar.y + indice.y) / 2


def mapear_a_pantalla(x_norm, y_norm):
    x = (x_norm - MARGEN) / (1 - 2 * MARGEN)
    y = (y_norm - MARGEN) / (1 - 2 * MARGEN)
    return x * ANCHO_PANTALLA, y * ALTO_PANTALLA


def limitar_a_pantalla(x, y):
    return (
        min(max(x, 1), ANCHO_PANTALLA - 2),
        min(max(y, 1), ALTO_PANTALLA - 2),
    )


def suavizar(anterior, objetivo):
    if anterior is None:
        return objetivo
    return (
        anterior[0] + (objetivo[0] - anterior[0]) * SUAVIZADO,
        anterior[1] + (objetivo[1] - anterior[1]) * SUAVIZADO,
    )


def dibujar_interfaz(frame, lm, dedos, estado, pinza_izq, ratio_izq, ratio_der, w, h):
    cv2.rectangle(
        frame,
        (int(MARGEN * w), int(MARGEN * h)),
        (int((1 - MARGEN) * w), int((1 - MARGEN) * h)),
        (200, 200, 0), 1
    )

    if lm is not None:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, lm, mp.solutions.hands.HAND_CONNECTIONS
        )

        for nombre, (punta, _) in DEDOS.items():
            p = lm.landmark[punta]
            color = (0, 255, 0) if dedos[nombre] else (0, 0, 255)
            cv2.circle(frame, (int(p.x * w), int(p.y * h)), 8, color, -1)

        cv2.putText(frame, f"Pinza izq: {ratio_izq:.2f}  der: {ratio_der:.2f}",
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if lm is None:
        texto, color = "NO HAY MANO", (0, 0, 255)
    elif estado == ESTADO_PAUSA:
        texto, color = "PAUSA (puno)", (0, 165, 255)
    elif estado == ESTADO_SCROLL:
        texto, color = "SCROLL", (255, 255, 0)
    elif pinza_izq:
        texto, color = "ARRASTRANDO / CLIC", (0, 255, 0)
    else:
        texto, color = "CURSOR", (255, 255, 255)

    cv2.putText(frame, texto, (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)


def main():
    mp_hands = mp.solutions.hands
    cap = cv2.VideoCapture(0)

    estado = ESTADO_CURSOR
    candidato = ESTADO_CURSOR
    frames_candidato = 0

    pinza_izq = False
    pinza_der = False

    cursor_suave = None
    offset = (0.0, 0.0)
    recalcular_offset = True

    scroll_y_anterior = None
    scroll_acumulado = 0.0

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("No se pudo leer la webcam")
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            lm = None
            dedos = {nombre: False for nombre in DEDOS}
            ratio_izq = ratio_der = 999

            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0]
                dedos = dedos_extendidos(lm, w, h)
                ratio_izq = calcular_ratio_pinza(lm, w, h, 8)
                ratio_der = calcular_ratio_pinza(lm, w, h, 12)

                pose = detectar_pose(dedos)
                if pose != estado:
                    if pose == candidato:
                        frames_candidato += 1
                    else:
                        candidato = pose
                        frames_candidato = 1
                    if frames_candidato >= FRAMES_CAMBIO_MODO and not pinza_izq and not pinza_der:
                        estado = pose
                        scroll_y_anterior = None
                        scroll_acumulado = 0.0
                        if estado == ESTADO_CURSOR:
                            recalcular_offset = True
                else:
                    candidato = estado
                    frames_candidato = 0

                if estado == ESTADO_CURSOR:
                    x_norm, y_norm = punto_control(lm)
                    bruto = mapear_a_pantalla(x_norm, y_norm)

                    if recalcular_offset:
                        pos = pyautogui.position()
                        offset = (pos.x - bruto[0], pos.y - bruto[1])
                        cursor_suave = (float(pos.x), float(pos.y))
                        recalcular_offset = False

                    objetivo = limitar_a_pantalla(bruto[0] + offset[0], bruto[1] + offset[1])
                    cursor_suave = suavizar(cursor_suave, objetivo)
                    pyautogui.moveTo(cursor_suave[0], cursor_suave[1])

                    if (not pinza_izq and ratio_izq < RATIO_PINZA_ON
                            and (dedos["corazon"] or dedos["anular"] or dedos["menique"])):
                        pinza_izq = True
                        pyautogui.mouseDown()
                    elif pinza_izq and ratio_izq > RATIO_PINZA_OFF:
                        pinza_izq = False
                        pyautogui.mouseUp()

                    if (not pinza_der and not pinza_izq
                            and ratio_der < RATIO_PINZA_ON and dedos["indice"]):
                        pinza_der = True
                        pyautogui.click(button="right")
                    elif pinza_der and ratio_der > RATIO_PINZA_OFF:
                        pinza_der = False

                elif estado == ESTADO_SCROLL:
                    y_muneca = lm.landmark[0].y
                    if scroll_y_anterior is not None:
                        delta = scroll_y_anterior - y_muneca
                        if abs(delta) > SCROLL_ZONA_MUERTA:
                            scroll_acumulado += delta * SCROLL_SENSIBILIDAD
                            pasos = int(scroll_acumulado)
                            if pasos != 0:
                                pyautogui.scroll(pasos)
                                scroll_acumulado -= pasos
                    scroll_y_anterior = y_muneca

            else:
                if pinza_izq:
                    pinza_izq = False
                    pyautogui.mouseUp()
                pinza_der = False
                estado = candidato = ESTADO_CURSOR
                frames_candidato = 0
                scroll_y_anterior = None
                recalcular_offset = True

            dibujar_interfaz(frame, lm, dedos, estado, pinza_izq, ratio_izq, ratio_der, w, h)
            cv2.imshow("Hand Mouse - 'q' para salir", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if pinza_izq:
        pyautogui.mouseUp()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
