import mailtrap as mt
#testo,password,mittente,destinatario
def sendGmail(testo,token,mittente,destinatario):
    mail = mt.Mail(
        sender=mt.Address(email=mittente, name="Mesh_controller"),
        to=[mt.Address(email=destinatario)],
        subject="Alert ch0",
        text=testo,
        category="Integration Test",
    )

    client = mt.MailtrapClient(token=token)
    response = client.send(mail)
    print(response)
