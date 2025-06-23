from pydantic import BaseModel, Field, validator


class BaseConfig(BaseModel):
    pop_size: int = Field(..., gt=0, description="Population size")
    sampling: Optional[Sampling] = None
    selection: Optional[Selection] = None
    crossover: Optional[Crossover] = None
    mutation: Optional[Mutation] = None
    survival: Optional[Survival] = None
    n_offsprings: Optional[int] = None
    eliminate_duplicates: Union[bool, DefaultDuplicateElimination, NoDuplicateElimination] = True
    repair: Optional[object] = None
    mating: Optional[object] = None
    advance_after_initial_infill: bool = False

    @validator("n_offsprings", always=True)
    def set_default_offsprings(cls, v, values):
        return v if v is not None else values.get("pop_size")

    @validator("eliminate_duplicates", pre=True)
    def resolve_duplicates(cls, v):
        if isinstance(v, bool):
            return DefaultDuplicateElimination() if v else NoDuplicateElimination()
        return v

    @validator("repair", always=True)
    def set_default_repair(cls, v):
        return v if v is not None else NoRepair()
