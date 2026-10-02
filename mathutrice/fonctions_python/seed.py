"""Seed reference data and development users into an empty database."""

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.database import engine
from mathutrice.referentiel import REFERENTIEL


NOTION_DESCRIPTIONS = {
    "trigonometrie": (
        "Étude des fonctions trigonométriques, des angles et du cercle "
        "trigonométrique."
    ),
    "fractions_puissances_radicaux": (
        "Manipulation des fractions, puissances et radicaux."
    ),
    "logarithme_exponentielle": (
        "Étude des fonctions logarithme et exponentielle."
    ),
    "manipulation_expressions_litterales": (
        "Isolement et manipulation de variables dans des expressions algébriques."
    ),
    "equations_inequations": (
        "Résolution d'équations et d'inéquations du premier et second degré."
    ),
    "polynomes_factorisation": (
        "Étude des polynômes, factorisation et identités remarquables."
    ),
    "analyse_dimensionnelle": (
        "Dimensions, unités et homogénéité des formules physiques."
    ),
}

DEVELOPMENT_USERS = (
    ("student@epfedu.fr", "Student", "Student"),
    ("teacher@epf.fr", "Teacher", "Teacher"),
    ("admin@epf.fr", "Admin", "Admin"),
)

SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    database_has_reference_data = any(
        session.exec(select(model)).first() is not None
        for model in (models.Notion, models.Competence, models.User)
    )

    if not database_has_reference_data:
        created_at = datetime.now(UTC)

        for email, name, role in DEVELOPMENT_USERS:
            session.add(
                models.User(
                    sso_id=uuid5(NAMESPACE_URL, f"mathutrice:user:{email}"),
                    created_at=created_at,
                    role=role,
                    email=email,
                    name=name,
                )
            )

        for referentiel_key, notion_data in REFERENTIEL.items():
            notion_id = uuid5(
                NAMESPACE_URL,
                f"mathutrice:notion:{referentiel_key}",
            )
            session.add(
                models.Notion(
                    notion_id=notion_id,
                    referentiel_key=referentiel_key,
                    title=notion_data["notion_nom"],
                    description=NOTION_DESCRIPTIONS[referentiel_key],
                )
            )

            for competence in notion_data["competences"]:
                code = competence["code"]
                session.add(
                    models.Competence(
                        competence_id=uuid5(
                            NAMESPACE_URL,
                            f"mathutrice:competence:{code}",
                        ),
                        referentiel_code=code,
                        title=competence["nom"],
                        level=competence["niveau"],
                        notion_id=notion_id,
                    )
                )

        session.commit()
